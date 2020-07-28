/****************************************************************************
*                CITYDECODER: A SPLAT! File Conversion Utility              *
*                  Copyright John A. Magliacane, KD2BD 2002                 *
*                         Last update: 20-May-2014                          *
*****************************************************************************
*                                                                           *
* This utility reads ASCII Metadata Cartographic Boundary Files available   *
* through the U.S. Census Bureau, and generates a lists of cities, states,  *
* counties, and county subdivisions along with the latitude and longitude   *
* corresponding to their geographic centers.  Such data may be (optionally) *
* sorted and written to files for use with SPLAT! software.  This utility   *
* takes as an argument, a two-letter prefix plus the FIPS code for the      *
* state being processed (ie: "citydecoder pl34" will read files             *
* "pl34_d00.dat" and "pl34_d00a.dat", and "citydecoder cs34" will read      *
* files "cs34_d00.dat" and "cs34_d00a.dat", and produce a list of city      *
* names and geographical coordinates for the state of New Jersey.           *
*                                                                           *
* ZIP compressed data files for the United States may be downloaded from:   *
*                                                                           *
* http://web.archive.org/web/20130331172800/http://www.census.gov/geo/www/cob/cs2000.html *
*                                                                           *
* Please select among the ARC/INFO Ungenerate (ASCII) formatted files at    *
* the bottom of each page, and use "unzip -a" or "gunzip" to properly       *
* unzip these files under Unix/Linux prior to use.                          *
*                                                                           *
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
*****************************************************************************
*          To compile: gcc -Wall -O3 -s citydecoder.c -o citydecoder        *
*****************************************************************************/

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

int main(argc,argv)
char argc, *argv[];
{
	int x, y, z;
	long attributefile_id, coordinatefile_id;
	char string[80], name[80], attributefilename[15], coordinatefilename[15];
	double lat, lon;
	FILE *attributefile=NULL, *coordinatefile=NULL;

	if (argc==1)
	{
		fprintf(stderr,"\n*** Usage: citydecoder pl34 cs34 pl42 cs42 | sort > outputfile\n\n");
		exit(1);
	}

	for (z=1; z<argc; z++)
	{
		sprintf(attributefilename,"%s_d00a.dat",argv[z]);
		sprintf(coordinatefilename,"%s_d00.dat",argv[z]);

		attributefile=fopen(attributefilename,"r");
		coordinatefile=fopen(coordinatefilename,"r");

		if (attributefile!=NULL && coordinatefile!=NULL)
		{
			/* Skip First ASCII File Record (ID=0) */

			for (x=0; x<7; x++)
				fgets(string,80,attributefile);

			/* Skip yet another line for "cs" files */

			if (argv[z][0]=='c' && argv[z][1]=='s')
				fgets(string,80,attributefile);
			do
			{
				string[0]=0;
				fscanf(coordinatefile,"%ld", &coordinatefile_id);

				if (coordinatefile_id!=-99999)
				{
					name[0]=0;

					fscanf(coordinatefile,"%lf %lf",&lon, &lat);

					/* Read ID Number From Attribute File */

					fgets(string,80,attributefile);
					sscanf(string,"%ld",&attributefile_id);

					/* Skip Several Strings in Attribute File */

					fgets(string,80,attributefile);
					fgets(string,80,attributefile);

					/* Skip a third line for "cs" files */

					if (argv[z][0]=='c' && argv[z][1]=='s')
						fgets(string,80,attributefile);

					/* Read City Name From Attribute File */

					fgets(string,80,attributefile);

					/* Strip "quote" characters from name */

					for (x=2, y=0; string[x]!='"' && string[x]!=0; x++, y++)
						name[y]=string[x];

					name[y]=0;

					/* Skip Two Strings in Attribute File */

					fgets(string,80,attributefile);
					fgets(string,80,attributefile);

					/* Skip blank line between records */

					fgets(string,80,attributefile);

					if (name[0]!=0 && name[0]!=' ' && feof(attributefile)==0 && attributefile_id==coordinatefile_id)
						printf("%s, %f, %f\n",name,lat,-lon);
				}


				/* Read to the end of the current coordinatefile record */

				do
				{
					string[0]=0;
					fscanf(coordinatefile,"%80s",string);

				} while (strncmp(string,"END",3)!=0 && feof(coordinatefile)==0);

			} while (feof(coordinatefile)==0);

			fclose(attributefile);
			fclose(coordinatefile);
		}

		else
		{
			/* Houston, We Have A Problem... */

			fprintf(stderr,"%c\n",7);

			if (coordinatefile==NULL)
				fprintf(stderr,"*** Error opening coordinate file: \"%s\"!\n",coordinatefilename);

			if (attributefile==NULL)
				fprintf(stderr,"*** Error opening attribute file : \"%s\"!\n",attributefilename);
			fprintf(stderr,"\n");
		}
	}
		
	exit(0);
}
