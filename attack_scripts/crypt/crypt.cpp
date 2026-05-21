#include "crypt.h"

// Randomly-generated key
char key[] = {'\xf1', '\xde', '\x8', '\x29', '\xc6', '\x3c', '\xb4', '\x37', '\xd0', '\xa6', '\xf5', '\xe3', '\xa4', '\x37', '\x4d', '\x1a', '\x7d', '\x6', '\x28', '\x83', '\x4f', '\xe1', '\x79', '\x41', '\xf0', '\x10', '\x89', '\xcf', '\x43', '\x65', '\x7e', '\x36', '\xc7', '\x83', '\x87', '\xde', '\x30', '\xaf', '\x3', '\x78', '\xa4', '\xb4', '\x20', '\xa9', '\x0', '\x96', '\xf6', '\xb7', '\xf2', '\x6c', '\xaf', '\x92', '\x9', '\xfa', '\x97', '\x8', '\x66', '\x87', '\x28', '\xad', '\xcf', '\xd', '\x32', '\x2e', '\xf7', '\xc6', '\x9b', '\x60', '\x55', '\x3a', '\xe2', '\x57', '\x85', '\xc4', '\xe3', '\xde', '\xa6', '\xd', '\xcb', '\x0', '\xcc', '\xcf', '\xa', '\xf1', '\xf3', '\x17', '\xcd', '\xab', '\x66', '\xfa', '\x5a', '\x93', '\x5f', '\xb6', '\xa1', '\xa', '\x9c', '\xf5', '\x69', '\xbc', '\x23', '\x11', '\x67', '\x27', '\x84', '\xf6', '\xac', '\xf', '\x32', '\xf', '\x2e', '\x58', '\x85', '\x1a', '\xd8', '\x42', '\x30', '\x4a', '\xa5', '\xd4', '\xd0', '\xc8', '\x9a', '\xee', '\x58', '\xb3', '\xf9', '\x30', '\x12', '\xe8', '\xd', '\xc', '\xa8', '\x1b', '\x8b', '\xa5', '\xb9', '\x41', '\x9b', '\xff', '\x2c', '\xb4', '\xff', '\xd2', '\x50', '\x10', '\xd1', '\xc5', '\x2a', '\xe4', '\x3e', '\xf2', '\x1d', '\x76', '\x13', '\x1b', '\x82', '\x62', '\x5d', '\x3a', '\x66', '\xaf', '\x95', '\xcc', '\xab', '\xf0', '\x9a', '\x62', '\xe3', '\xf4', '\xef', '\xa', '\xe', '\x88', '\xd0', '\x89', '\x2c', '\xaa', '\x60', '\x3e', '\xe8', '\x72', '\xb2', '\x43', '\xec', '\xd6', '\x5b', '\xc4', '\x9f', '\xe2', '\x43', '\xf2', '\xae', '\xdc', '\x63', '\x16', '\x49', '\x49', '\x8f', '\x54', '\x8', '\x0', '\xd8', '\xf5', '\x6e', '\xb9', '\x4f', '\xdc', '\x31', '\x9', '\x59', '\x84', '\x2e', '\x56', '\x35', '\xf4', '\x49', '\x1b', '\xc2', '\xe4', '\x45', '\xd2', '\x6c', '\xe2', '\xa2', '\x4a', '\x23', '\xa6', '\x90', '\xa5', '\x14', '\xf3', '\x1a', '\xb6', '\x5e', '\x1', '\x1e', '\x3f', '\xdc', '\x1f', '\x24', '\x3e', '\x2d', '\x8c', '\x1b', '\x2c', '\x9e', '\x2c', '\x1', '\xff', '\xf6', '\xf9', '\x7c', '\x4', '\x4d', '\x17'};

int byteCounter;

int main(int argc, char** argv) {
	if (argc == 2) {
		run(string(argv[1]), 0, string(argv[0]));
		return 0;
	} else if (argc == 3) {
		int minSeconds = atoi(argv[2]);
		if (minSeconds > 0) {
			run(string(argv[1]), minSeconds, string(argv[0]));
		} else {
			argError(argv);
		}
	} else {
		argError(argv);
	}
}

void run(string filename, int minSeconds, string argv0) {
	if (filename == argv0) {
		// To prevent accidental encryption of all the files in the working directory
		cout << "The program cannot be run on the current folder" << endl;
		exit(1);
	}

	chrono::milliseconds startTime = currentTimeMs();
	int iterations = 0;
	bool proceed;
	do {
		byteCounter = 0;
		runDirectory(filename);

		auto elapsed = (currentTimeMs() - startTime).count();
#ifdef DEBUG
		cout << "Elapsed: " << elapsed << ", remaining: " << minSeconds * 1000 - elapsed << endl;
#endif
		proceed = elapsed < minSeconds * 1000;
		iterations++;
	} while (proceed);

#ifdef DEBUG
	auto elapsed = (currentTimeMs() - startTime).count();
	float timePerIteration = elapsed / (float) iterations;
	cout << "Average time per iteration: " << timePerIteration << endl;
#endif
}

void runDirectory(string dirPath) {
	// Remove trailing optional slash to ensure consistency
	if (dirPath.at(dirPath.length() - 1) == '/') {
		dirPath = dirPath.substr(0, dirPath.length() - 1);
	}

	DIR *dir;
	struct dirent *dirent;

	if ((dir = opendir(dirPath.c_str())) != NULL) {
		while ((dirent = readdir(dir)) != NULL) {
			string filename = string(dirent->d_name);
			string filePath = dirPath + "/" + filename;
			if (filename != "." && filename != "..") {
#ifdef DEBUG
				cout << filePath << endl;
#endif
				if (dirent->d_type == DT_DIR) {
					runDirectory(filePath);
				} else if (dirent->d_type == DT_REG) {
					fstream stream;
					stream.open(filePath, ios::in | ios::out | ios::binary);

					if (stream.is_open() && stream.good()) {
						char byte;
						while (stream.get(byte)) {
							stream.seekp(stream.tellg() - (std::streamoff) 1);
							stream.put(byte ^ key[byteCounter % sizeof(key)]);
							byteCounter++;
						}
					}
					stream.close();
				}
			}
		}
	} else {
		cout << "Error: Cannot open " << dirPath << endl;
		exit(1);
	}
}

void argError(char** argv) {
	cout << "Usage: " << argv[0] << " file [min_seconds = 0]" << endl;
	cout << "Encrypts <file>. If <file> is a directory, recursively encrypts all the files in it. The program uses " <<
		"a XOR cypher, so running it again on the same files decrypts them." << endl;
	cout << "min_seconds: Minimum execution time, in seconds. Multiple iterations will be performed until " <<
		"this duration is reached. If unspecified, only one iteration will be performed." << endl;
	exit(1);
}

chrono::milliseconds currentTimeMs() {
	return chrono::duration_cast<chrono::milliseconds> (chrono::system_clock::now().time_since_epoch());
}