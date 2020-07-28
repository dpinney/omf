/***************************************************************************\
*     bearing: Determines distance and azimuth bearing between locations    *
*                     specified in a pair of .qth files                     *
*			  Last update: 08-Jan-2014			    *
*****************************************************************************
*      Project started on December 7, 2007 by John A. Magliacane, KD2BD     *
*****************************************************************************
*                                                                           *
* This program is free software; you can redistribute it and/or modify it   *
* under the terms of the GNU General Public License as published by the     *
* Free Software Foundation; either version 2 of the License or any later    *
* version.								    *
*									    *
* This program is distributed in the hope that it will useful, but WITHOUT  *
* ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or     *
* FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License     *
* for more details.							    *
*									    *
*****************************************************************************
*      gcc -Wall -O3 -s -lm -fomit-frame-pointer bearing.c -o bearing       *
\***************************************************************************/

#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <unistd.h>

char 	string[255];

double	TWOPI=6.283185307179586, PI=3.141592653589793,
	deg2rad=1.74532925199e-02, KM_PER_MILE=1.609344;

struct site {	double lat;
		double lon;
		double azimuth;
		char name[50];
	    } 	site;


double arccos(double x, double y)
{
	/* This function implements the arc cosine function,
	   returning a value between 0 and TWOPI. */

	double result=0.0;

	if (y>0.0)
		result=acos(x/y);

	if (y<0.0)
		result=PI+acos(x/y);

	return result;
}

char *dec2dms(double decimal)
{
	/* Converts decimal degrees to degrees, minutes, seconds,
	   (DMS) and returns the result as a character string. */

	char	sign;
	int	degrees, minutes, seconds;
	double	a, b, c, d;

	if (decimal<0.0)
	{
		decimal=-decimal;
		sign=-1;
	}

	else
		sign=1;

	a=floor(decimal);
	b=60.0*(decimal-a);
	c=floor(b);
	d=60.0*(b-c);

	degrees=(int)a;
	minutes=(int)c;
	seconds=(int)d;

	if (seconds<0)
		seconds=0;

	if (seconds>59)
		seconds=59;

	string[0]=0;
	sprintf(string,"%d%c %d\' %d\"", degrees*sign, 176, minutes, seconds);
	return (string);
}

double Distance(struct site site1, struct site site2)
{
	/* This function returns the great circle distance
	   in miles between any two site locations. */

	double	lat1, lon1, lat2, lon2, distance;

	lat1=site1.lat*deg2rad;
	lon1=site1.lon*deg2rad;
	lat2=site2.lat*deg2rad;
	lon2=site2.lon*deg2rad;

	distance=3959.0*acos(sin(lat1)*sin(lat2)+cos(lat1)*cos(lat2)*cos((lon1)-(lon2)));

	return distance;
}

double Azimuth(struct site source, struct site destination)
{
	/* This function returns the azimuth (in degrees) to the
	   destination as seen from the location of the source. */

	double	dest_lat, dest_lon, src_lat, src_lon,
		beta, azimuth, diff, num, den, fraction;

	dest_lat=destination.lat*deg2rad;
	dest_lon=destination.lon*deg2rad;

	src_lat=source.lat*deg2rad;
	src_lon=source.lon*deg2rad;
		
	/* Calculate Surface Distance */

	beta=acos(sin(src_lat)*sin(dest_lat)+cos(src_lat)*cos(dest_lat)*cos(src_lon-dest_lon));

	/* Calculate Azimuth */

	num=sin(dest_lat)-(sin(src_lat)*cos(beta));
	den=cos(src_lat)*sin(beta);
	fraction=num/den;

	/* Trap potential problems in acos() due to rounding */

	if (fraction>=1.0)
		fraction=1.0;

	if (fraction<=-1.0)
		fraction=-1.0;

	/* Calculate azimuth */

	azimuth=acos(fraction);

	/* Reference it to True North */

	diff=dest_lon-src_lon;

	if (diff<=-PI)
		diff+=TWOPI;

	if (diff>=PI)
		diff-=TWOPI;

	if (diff>0.0)
		azimuth=TWOPI-azimuth;

	return (azimuth/deg2rad);		
}

double ReadBearing(char *input)
{
	/* This function takes numeric input in the form of a character
	   string, and returns an equivalent bearing in degrees as a
	   decimal number (double).  The input may either be expressed
	   in decimal format (40.139722) or degree, minute, second
	   format (40 08 23).  This function also safely handles
	   extra spaces found either leading, trailing, or
	   embedded within the numbers expressed in the
	   input string.  Decimal seconds are permitted. */
 
	double	seconds, bearing=0.0;
	char	string[20];
	int	a, b, length, degrees, minutes;

	/* Copy "input" to "string", and ignore any extra
	   spaces that might be present in the process. */

	string[0]=0;
	length=strlen(input);

	for (a=0, b=0; a<length && a<18; a++)
	{
		if ((input[a]!=32 && input[a]!='\n') || (input[a]==32 && input[a+1]!=32 && input[a+1]!='\n' && b!=0))
		{
			string[b]=input[a];
			b++;
		}	 
	}

	string[b]=0;

	/* Count number of spaces in the clean string. */

	length=strlen(string);

	for (a=0, b=0; a<length; a++)
		if (string[a]==32)
			b++;

	if (b==0)  /* Decimal Format (40.139722) */
		sscanf(string,"%lf",&bearing);

	if (b==2)  /* Degree, Minute, Second Format (40 08 23.xx) */
	{
		sscanf(string,"%d %d %lf",&degrees, &minutes, &seconds);

		bearing=fabs((double)degrees);
		bearing+=fabs(((double)minutes)/60.0);
		bearing+=fabs(seconds/3600.0);

		if ((degrees<0) || (minutes<0) || (seconds<0.0))
			bearing=-bearing;
	}

	/* Anything else returns a 0.0 */

	if (bearing>360.0 || bearing<-90.0)
		bearing=0.0;

	return bearing;
}

struct site LoadQTH(char *filename)
{
	/* This function reads SPLAT! .qth (site location) files.
	   The latitude and longitude may be expressed either in
	   decimal degrees, or in degree, minute, second format.
	   Antenna height is assumed to be expressed in feet above
	   ground level (AGL), unless followed by the letter 'M',
	   or 'm', or by the word "meters" or "Meters", in which
	   case meters is assumed, and is handled accordingly. */

	int	x;
	char	string[50], qthfile[255];
	struct	site tempsite;
	FILE	*fd=NULL;

	for (x=0; filename[x]!='.' && filename[x]!=0 && x<250; x++)
		qthfile[x]=filename[x];

	qthfile[x]='.';
	qthfile[x+1]='q';
	qthfile[x+2]='t';
	qthfile[x+3]='h';
	qthfile[x+4]=0;

	tempsite.lat=91.0;
	tempsite.lon=361.0;
	tempsite.name[0]=0;
	tempsite.azimuth=0.0;

	fd=fopen(qthfile,"r");

	if (fd!=NULL)
	{
		/* Site Name */
		fgets(string,49,fd);

		/* Strip <CR> and/or <LF> from end of site name */

		for (x=0; string[x]!=13 && string[x]!=10 && string[x]!=0; tempsite.name[x]=string[x], x++);

		tempsite.name[x]=0;

		/* Site Latitude */
		fgets(string,49,fd);
		tempsite.lat=ReadBearing(string);

		/* Site Longitude */
		fgets(string,49,fd);
		tempsite.lon=ReadBearing(string);

		fclose(fd);
	}

	return tempsite;
}

int main(int argc, char *argv[])
{
	int		x, y;
	unsigned char	sitenum, metric, error;
	double		distance, azimuth;
	struct		site point[2];

	if (argc==1)
	{
		fprintf(stdout,"\nProvides distance and azimuth bearing between two site locations.\n");
		fprintf(stdout,"\nUsage: bearing site1(.qth) site2(.qth)");
		fprintf(stdout,"\n       bearing site1(.qth) site2(.qth) -metric\n\n");
		fflush(stdout);
		return 1;
	}

	metric=0;
	error=0;
	y=argc-1;
	sitenum=0;

	point[0].lat=91.0;
	point[0].lon=361.0;
	point[1].lat=91.0;
	point[1].lon=361.0;

	/* Scan for command line arguments */

	for (x=1; x<=y; x++)
	{
		if (strcmp(argv[x],"-metric")==0)
		{
			metric=1;
			x++;
		}

		/* Read Receiver Location */

		if (x<=y && argv[x][0] && argv[x][0]!='-' && sitenum<2)
		{
			point[sitenum]=LoadQTH(argv[x]);

			if (point[sitenum].lat>90.0 || point[sitenum].lon>360.0)
				fprintf(stderr,"\n%c*** \"%s\" is not a valid .qth file!",7,argv[x]);
			else
				sitenum++;
		}
	}

	if (sitenum<2)
	{
		fprintf(stderr,"\n%c*** ERROR: Not enough valid sites specified!\n\n",7);
		exit (-1);
	}

	for (x=0; x<sitenum; x++)
	{
		if (point[x].lat>90.0 && point[x].lon>360.0)
		{
			fprintf(stderr,"\n*** ERROR: site #%d not found!",x+1);
			error=1;
		}
	}

	if (error)
		return -1;

	else
	{
		/* Perform the calculations and display the results */

		distance=Distance(point[0],point[1]);
		azimuth=Azimuth(point[0],point[1]);

		printf("\nThe distance between %s and %s is\n",point[0].name, point[1].name);

		if (metric)
			printf("%.2f kilometers",distance*KM_PER_MILE);
		else
			printf("%.2f miles",distance);

		printf(" at a bearing of %.2f%c azimuth.\n\n",azimuth, 176);
	}

	return 0;
}
