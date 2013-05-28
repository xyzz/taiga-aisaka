#include <iostream>
#include <fstream>
#include <string>
#include <sstream>
#include <stdio.h>
#include <string.h>

#define _int32 int
#define _int64 long long

using namespace std;

struct EntryStruct
{
	unsigned _int32 EntryOffset;
	int EntrySize;
	int EntryNameOffset;
};

void ParseGPDA(unsigned _int32, int);
void ReadUnknown();

ifstream InMap;
ifstream InRes;
ofstream OutFile;

int main(int argc, const char* argv[])
{
	
	InMap.open("seekmap.txt", ios::in);
	InRes.open("RES.dat", ios::in | ios::binary);
	OutFile.open("seekmap.new", ios::out | ios::trunc);

	if (!InMap)
    {
        cout << "Could not open seekmap.txt\n";
        return -1;
    }

	if (!InRes)
    {
        cout << "Could not open RES.dat\n";
        return -1;
    }

	if (!OutFile)
	{
		cout << "Unable to write to seekmap.new\n";
		return -1;
	}

	OutFile << "resource.dat 0 ";
	ParseGPDA(0, 1);

	return 0;
}

void ParseGPDA(unsigned _int32 CurrOffset, int Nesting)
{
	char Pad[4];
	unsigned _int32 ArchiveSize = 0;
	int Entries = 0;

	InRes.seekg(CurrOffset);

	InRes.read(Pad, 4);
	InRes.read((char*)&ArchiveSize, 4);
	InRes.read(Pad, 4);
	InRes.read((char*)&Entries, 4);

	OutFile << dec << ArchiveSize << " ";
	ReadUnknown();
	OutFile << " 0 " << Entries << " \r\n";

	EntryStruct *EntryArray;
	EntryArray = new EntryStruct[Entries];

	string *FileNames;

	FileNames = new string[Entries];

	//Read EntryHeader
	for(int Entry=0; Entry<Entries; Entry++)
	{
		unsigned _int32 EntryOffset;
		int EntrySize;
		int EntryNameOffset;

		InRes.read((char*)&EntryOffset, 4);
		InRes.read(Pad, 4);
		InRes.read((char*)&EntrySize, 4);
		InRes.read((char*)&EntryNameOffset, 4);

		EntryArray[Entry].EntryOffset = EntryOffset;
		EntryArray[Entry].EntrySize = EntrySize;
		EntryArray[Entry].EntryNameOffset = EntryNameOffset;
	}

	// Read FileName header
	for(int Entry=0; Entry<Entries; Entry++)
	{
		int NameSize = 0;

		InRes.read((char*)&NameSize, 4);

		char *FileName;
		FileName = new char[NameSize + 1];

		InRes.read(FileName, NameSize);

		FileName[NameSize] = '\0';

		FileNames[Entry] = FileName;
	}

	for(int x=0; x<Entries; x++)
	{
		unsigned _int32 TotalOffset = CurrOffset + EntryArray[x].EntryOffset;

		for(int y=0; y<Nesting; y++)
			OutFile << '\t';

		//Is this entry also a GPDA? If so recurse this function on it
		char Sig[4] = {0x00, 0x00, 0x00, 0x00};
		
		InRes.seekg(TotalOffset);
		InRes.read(Sig, 4);
			
		if ( strncmp(Sig, "GPDA", 4) == 0 )
		{
			OutFile << FileNames[x] << " " << dec << TotalOffset << " ";
			ParseGPDA(TotalOffset, (Nesting+1) );
		}
		else
		{
			OutFile << FileNames[x] << " " << dec << TotalOffset << " " << dec << EntryArray[x].EntrySize << " ";
			ReadUnknown();
			OutFile << " \r\n";
		}
	}

	delete [] EntryArray;
	delete [] FileNames;

}

void ReadUnknown()
{
	// Not sure what the third number in the seekmap is, so I'll just copy the existing one
	InMap.ignore(100, ' ');

	unsigned _int64 Unknown = 0;
	InMap >> Unknown;
	InMap >> Unknown;
	InMap >> Unknown;

	InMap.ignore(100, '\n');

	OutFile << Unknown;

}


