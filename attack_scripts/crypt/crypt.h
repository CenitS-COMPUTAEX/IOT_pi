#include <iostream>
#include <fstream>
#include <string>
#include <chrono>
#include <sys/types.h>
#include <dirent.h>
#include <libgen.h>
using namespace std;

int main(int argc, char** argv);
void run(string filename, int minSeconds, string argv0);
void runDirectory(string dirPath);
void argError(char** argv);
chrono::milliseconds currentTimeMs();