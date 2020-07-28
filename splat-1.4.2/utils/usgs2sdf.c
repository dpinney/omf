/****************************************************************************
*            USGS2SDF: USGS to SPLAT Data File Converter Utility            *
*               Copyright John A. Magliacane, KD2BD 1997-2014               *
*                         Last update: 08-Mar-2014                          *
*****************************************************************************
*                                                                           *
* This program reads files containing delimited US Geological Survey        *
* Digital Elevation Model Data files, and creates Splat Data Files          *
* containing ONLY the raw information needed by SPLAT!, thereby saving      *
* disk space, as well as read/write time.                                   *
*                                                                           *
* The format of .sdf files created by this utility is as follows:           *
*                                                                           *
*	maximum west longitude (degrees West)                               *
*	minimum north latitude (degrees North)                              *
*	minimum west longitude (degrees West)                               *
*	maximum north latitude (degrees North)                              *
*       ...1440000 elevation points... (1200x1200)                          *
*                                                                           *
* All data is represented as integers.  A single '\n' follows each value.   *
*                                                                           *
* SPLAT Data Files are named according to the geographical locations        *
* they represent (ie: min_north:max_north:min_west:max_west.sdf).           *
*                                                                           *
*****************************************************************************
*          To compile: gcc -Wall -O6 -s splat2sdf.c -o splat2sdf            *
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
#include <stdlib.h>

char *d2e(string)
char *string;
{
	/* This function is used to replace 'D's with 'E's for proper
	   exponential notation of numeric strings read from delimited
	   USGS data files.  It returns a pointer to a string. */

	unsigned char x;

	for (x=0; string[x]!=0; x++)
		if (string[x]=='D')
			string[x]='E';
	return (string);
}

int main(argc,argv)
int argc;
char *argv[];
{
	unsigned char minimum[30], maximum[30], swlong[30],
		 swlat[30], nelong[30], nelat[30];
		/* nwlat[30], nwlong[30], selong[30], selat[30]; */
	char string[40];
	double max_el, min_el,  max_west, min_west, max_north, min_north;
	int x, y, z, c, array[1202][1202];
	char splatfile[25];
	FILE *fd;

	if (argc!=2)
	{
		fprintf(stderr,"Usage: usgs2sdf uncompressed_delimited_usgs_datafile (ie: wilmington-e)\n");
		exit(0);
	}

	fd=fopen(argv[1],"rb");

	if (fd!=NULL)
	{
		fprintf(stdout,"Reading \"%s\"...",argv[1]);
		fflush(stdout);

		/* Skip first 548 bytes */

		for (x=0; x<548; x++)
			getc(fd);

		/* Read quadrangle corners */
	
		/* Read southwest longitude */

		for (x=0; x<22; x++)
			swlong[x]=getc(fd);
		swlong[x]=0;

		/* Skip 2 bytes */

		for (x=0; x<2; x++)
			getc(fd);

		/* Read southwest latitude */

		for (x=0; x<22; x++)
			swlat[x]=getc(fd);
		swlat[x]=0;

		/* Skip 2 bytes */

		for (x=0; x<2; x++)
			getc(fd);

		/* Read northwest longitude */

		/**
		for (x=0; x<22; x++)
			nwlong[x]=getc(fd);
		nwlong[x]=0;
		**/

		for (x=0; x<22; x++)
			getc(fd);

		/* Skip 2 bytes */

		for (x=0; x<2; x++)
			getc(fd);

		/* Read northwest latitude */

		/**
		for (x=0; x<22; x++)
			nwlat[x]=getc(fd);
		nwlat[x]=0;
		**/

		for (x=0; x<22; x++)
			getc(fd);

		/* Skip 2 bytes */

		for (x=0; x<2; x++)
			getc(fd);

		/* Read northeast longitude */

		for (x=0; x<22; x++)
			nelong[x]=getc(fd);
		nelong[x]=0;

		/* Skip 2 bytes */

		for (x=0; x<2; x++)
			getc(fd);

		/* Read northeast latitude */

		for (x=0; x<22; x++)
			nelat[x]=getc(fd);
		nelat[x]=0;

		/* Skip 2 bytes */

		for (x=0; x<2; x++)
			getc(fd);

		/* Read southeast longitude */

		/**
		for (x=0; x<22; x++)
			selong[x]=getc(fd);
		selong[x]=0;
		**/

		for (x=0; x<22; x++)
			getc(fd);

		/* Skip 2 bytes */

		for (x=0; x<2; x++)
			getc(fd);

		/* Read southeast latitude */

		/**
		for (x=0; x<22; x++)
			selat[x]=getc(fd);
		selat[x]=0;
		**/

		for (x=0; x<22; x++)
			getc(fd);

		/* Skip 2 bytes */

		for (x=0; x<2; x++)
			getc(fd);

		/* Read minimum elevation */ 

		for (x=0; x<22; x++)
			minimum[x]=getc(fd);
		minimum[x]=0;

		/* Skip 2 bytes */

		for (x=0; x<2; x++)
			getc(fd);

		/* Read maximum elevation */

		for (x=0; x<22; x++)
			maximum[x]=getc(fd);

		maximum[x]=0;

		sscanf(d2e((char*)minimum),"%lG",&min_el);
		sscanf(d2e((char*)maximum),"%lf",&max_el);

		sscanf(d2e((char*)swlong),"%lf",&max_west);
		sscanf(d2e((char*)swlat),"%lf",&min_north);

		sscanf(d2e((char*)nelong),"%lf",&min_west);
		sscanf(d2e((char*)nelat),"%lf",&max_north);

		max_west/=-3600.0;
		min_north/=3600.0;
		max_north/=3600.0;
		min_west/=-3600.0;

		/* Skip 84 Bytes */

		for (x=0; x<84; x++)
			getc(fd);

		/* Read elevation data... */

		for (x=1200; x>=0; x--)
		{
			if (x==900)
			{
				printf(" 25%c...",37);
				fflush(stdout);
			}

			if (x==600)
			{
				printf(" 50%c...",37);
				fflush(stdout);
			}

			if (x==300)
			{
				printf(" 75%c... ",37);
				fflush(stdout);
			}

			/* Skip over 9 strings of data */

			for (y=0; y<9; y++)
			{
				string[0]=0;

				do
				{
					c=getc(fd);

				} while (c==' ' || c=='\n');

				for (z=0; c!=' ' && c!='\n' && z<28; z++)
				{
					string[z]=c;
					c=getc(fd);
				}

				string[z]=0;	
			}

			/* Store elevation data in array */

			for (y=0; y<1201; y++)
			{
				string[0]=0;

				do
				{
					c=getc(fd);

				} while (c==' ' || c=='\n');

				for (z=0; c!=' ' && c!='\n' && z<28; z++)
				{
					string[z]=c;
					c=getc(fd);
				}

				string[z]=0;	
				sscanf(string,"%d",&array[y][x]);
			}
		}

		fclose(fd);

		/* Write splat data file to disk */

		sprintf(splatfile,"%.0f:%.0f:%.0f:%.0f.sdf",min_north,max_north,min_west,max_west);

		fprintf(stdout," Done!\nWriting \"%s\"... ",splatfile);
		fflush(stdout);

		fd=fopen(splatfile,"w");

		fprintf(fd,"%.0f\n%.0f\n%.0f\n%.0f\n", max_west, min_north, min_west, max_north);

		for (x=0; x<1200; x++)
			for (y=0; y<1200; y++)
				fprintf(fd,"%d\n",array[x][y]);

		fclose(fd);
		fprintf(stdout,"Done!\n");
		fflush(stdout);
	}

	if (fd==NULL)
	{
		fprintf(stderr,"*** %c%s%c: File Not Found!\n",34,argv[1],34);
		exit(-1);
	}
	else
		exit(0);
}
