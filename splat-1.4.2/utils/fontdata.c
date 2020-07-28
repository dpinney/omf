/****************************************************************************
*                  FONTDATA:  A "fontdata.h" File Generator                 *
*                  Copyright John A. Magliacane, KD2BD 2002                 *
*                         Last update: 08-Jan-2014                          *
*****************************************************************************
*                                                                           *
* This utility reads gzip compressed font data, and generates a fontdata.h  *
* file required for compilation of SPLAT!.  Slackware Linux users may       *
* find compatible console font data files under /usr/lib/kbd/consolefonts   *
* (Slackware < version 8), or /usr/share/kbd/consolefonts (Slackware 8).    *
*                                                                           *
*                       Example: fontdata s.fnt.gz                          *
*   Writes s.fnt font data to "fontdata.h" in current working directory.    *
*                                                                           *
*****************************************************************************
*          To compile: gcc -Wall -O3 -s -lz fontdata.c -o fontdata          *
*****************************************************************************
*                                                                           *
* This program is free software; you can redistribute it and/or modify it   *
* under the terms of the GNU General Public License as published by the     *
* Free Software Foundation; either version 2 of the License or any later    *
* version.                                                                  *
*                                                                           *
* This program is distributed in the hope that it will useful, but WITHOUT  *
* ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or     *
* FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License     *
* for more details.                                                         *
*                                                                           *
*****************************************************************************/

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <zlib.h>

int main(argc,argv)
int argc;
char *argv[];
{
	int x, input;
	unsigned char line;
	FILE *outfile;
	gzFile *infile=Z_NULL;
	
	if (argc==2)
		*infile=gzopen(argv[1],"rb");

	else
	{	
		fprintf(stderr,"Usage: fontdata fontfile.gz\n");
		exit(-1);
	}

	if (infile!=Z_NULL)
	{
		outfile=fopen("fontdata.h","wb");

		fprintf(outfile,"static unsigned char fontdata[] = {\n  ");

		for (x=0, line=0; x<4096; x++)
		{
			input=gzgetc((gzFile)infile);
			
			fprintf(outfile," 0x%.2x",(unsigned char)input);
	   		line++;

			if (x<4095)
				fprintf(outfile,",");

			if (line==12)
			{
				fprintf(outfile,"\n  ");
				line=0;
			}
		}

	 	fprintf(outfile," };\n");

		gzclose((gzFile)infile);
		fclose(outfile);

		printf("fontdata.h successfully written!\n");
	}

	else
	{
		fprintf(stderr,"%c*** Error: %c%s%c Not Found!\n",7,34,argv[1],34);
		exit(-1);
	}

	exit(0);
}
