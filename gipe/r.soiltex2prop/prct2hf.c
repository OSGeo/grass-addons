#include<stdio.h>

#define POLYGON_DIMENSION 50

struct vector{
	double sand;
	double clay;
	double silt;
};


// HF

double prct2hf(double sand_input, double clay_input){
	int i,index;
	double temp, hf;
	double silt_input=0.0; 	//Rawls et al (1990)
				//do not have silt input
	// set up mark index for inside/outside polygon check
	double mark[POLYGON_DIMENSION]={0.0};
	//printf("in prct2hf(), cm\n");
	//setup the 3Dvectors and initialize them
	struct vector cls[POLYGON_DIMENSION] = {0.0};
	//In case silt is not == 0.0, fill up explicitly
	for(i=0;i<POLYGON_DIMENSION;i++){
		cls[i].sand=0.0;
		cls[i].clay=0.0;
		cls[i].silt=0.0;
	}
	//transform input from [0,1] to [0,100]
	sand_input *= 100.0;
	clay_input *= 100.0;
	//fill up initial polygon points
	cls[0].sand=0.0;
	cls[0].clay=100.0;
	cls[1].sand=0.0;
	cls[1].clay=54.0;
	cls[2].sand=17.0;
	cls[2].clay=55.0;
	//Get started
	mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
	if(mark[0]==1){
		hf=175.0;
		index=1;
		//printf("hf=175.0\n");
	}
	if (index==0){// if index not found then continue
		cls[0].sand=0.0;
		cls[0].clay=100.0;
		cls[1].sand=17.0;
		cls[1].clay=55.0;
		cls[2].sand=30.0;
		cls[2].clay=60.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=175.0\n");
			hf=175.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=0.0;
		cls[0].clay=100.0;
		cls[1].sand=34.0;
		cls[1].clay=66.0;
		cls[2].sand=30.0;
		cls[2].clay=60.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=175.0\n");
			hf=175.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=100.0;
		cls[0].clay=0.0;
		cls[1].sand=72.0;
		cls[1].clay=0.0;
		cls[2].sand=65.0;
		cls[2].clay=15.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=5.0\n");
			hf=5.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=100.0;
		cls[0].clay=0.0;
		cls[1].sand=65.0;
		cls[1].clay=30.0;
		cls[2].sand=65.0;
		cls[2].clay=15.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=5.0\n");
			hf=5.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=100.0;
		cls[0].clay=0.0;
		cls[1].sand=65.0;
		cls[1].clay=30.0;
		cls[2].sand=67.0;
		cls[2].clay=33.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=5.0\n");
			hf=5.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=58.0;
		cls[0].clay=42.0;
		cls[1].sand=65.0;
		cls[1].clay=30.0;
		cls[2].sand=67.0;
		cls[2].clay=33.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=15.0\n");
			hf=15.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=58.0;
		cls[0].clay=42.0;
		cls[1].sand=65.0;
		cls[1].clay=30.0;
		cls[2].sand=30.0;
		cls[2].clay=0.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=15.0\n");
			hf=15.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=65.0;
		cls[0].clay=15.0;
		cls[1].sand=65.0;
		cls[1].clay=30.0;
		cls[2].sand=30.0;
		cls[2].clay=0.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=15.0\n");
			hf=15.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=65.0;
		cls[0].clay=15.0;
		cls[1].sand=72.0;
		cls[1].clay=0.0;
		cls[2].sand=30.0;
		cls[2].clay=0.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=15.0\n");
			hf=15.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=16.0;
		cls[0].clay=0.0;
		cls[1].sand=20.0;
		cls[1].clay=14.0;
		cls[2].sand=30.0;
		cls[2].clay=0.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=25.0\n");
			hf=25.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=28.0;
		cls[0].clay=24.0;
		cls[1].sand=20.0;
		cls[1].clay=14.0;
		cls[2].sand=30.0;
		cls[2].clay=0.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=25.0\n");
			hf=25.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=28.0;
		cls[0].clay=24.0;
		cls[1].sand=58.0;
		cls[1].clay=42.0;
		cls[2].sand=30.0;
		cls[2].clay=0.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=25.0\n");
			hf=25.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=28.0;
		cls[0].clay=24.0;
		cls[1].sand=58.0;
		cls[1].clay=42.0;
		cls[2].sand=55.0;
		cls[2].clay=45.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=25.0\n");
			hf=25.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=55.0;
		cls[0].clay=45.0;
		cls[1].sand=50.0;
		cls[1].clay=50.0;
		cls[2].sand=35.0;
		cls[2].clay=42.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=35.0\n");
			hf=35.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=55.0;
		cls[0].clay=45.0;
		cls[1].sand=28.0;
		cls[1].clay=24.0;
		cls[2].sand=35.0;
		cls[2].clay=42.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=35.0\n");
			hf=35.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=20.0;
		cls[0].clay=28.0;
		cls[1].sand=28.0;
		cls[1].clay=24.0;
		cls[2].sand=35.0;
		cls[2].clay=42.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=35.0\n");
			hf=35.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=20.0;
		cls[0].clay=28.0;
		cls[1].sand=28.0;
		cls[1].clay=24.0;
		cls[2].sand=20.0;
		cls[2].clay=14.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=35.0\n");
			hf=35.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=20.0;
		cls[0].clay=28.0;
		cls[1].sand=10.0;
		cls[1].clay=14.0;
		cls[2].sand=20.0;
		cls[2].clay=14.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=35.0\n");
			hf=35.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=16.0;
		cls[0].clay=0.0;
		cls[1].sand=10.0;
		cls[1].clay=14.0;
		cls[2].sand=20.0;
		cls[2].clay=14.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=35.0\n");
			hf=35.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=16.0;
		cls[0].clay=0.0;
		cls[1].sand=10.0;
		cls[1].clay=14.0;
		cls[2].sand=7.0;
		cls[2].clay=3.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=35.0\n");
			hf=35.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=16.0;
		cls[0].clay=0.0;
		cls[1].sand=0.0;
		cls[1].clay=0.0;
		cls[2].sand=7.0;
		cls[2].clay=3.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=35.0\n");
			hf=35.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=3.0;
		cls[0].clay=3.0;
		cls[1].sand=0.0;
		cls[1].clay=0.0;
		cls[2].sand=7.0;
		cls[2].clay=3.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=35.0\n");
			hf=35.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=3.0;
		cls[0].clay=3.0;
		cls[1].sand=0.0;
		cls[1].clay=0.0;
		cls[2].sand=0.0;
		cls[2].clay=9.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=35.0\n");
			hf=35.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=3.0;
		cls[0].clay=3.0;
		cls[1].sand=0.0;
		cls[1].clay=28.0;
		cls[2].sand=0.0;
		cls[2].clay=9.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=50.0\n");
			hf=50.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=3.0;
		cls[0].clay=3.0;
		cls[1].sand=0.0;
		cls[1].clay=28.0;
		cls[2].sand=7.0;
		cls[2].clay=3.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=50.0\n");
			hf=50.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=10.0;
		cls[0].clay=14.0;
		cls[1].sand=0.0;
		cls[1].clay=28.0;
		cls[2].sand=7.0;
		cls[2].clay=3.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=50.0\n");
			hf=50.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=10.0;
		cls[0].clay=14.0;
		cls[1].sand=0.0;
		cls[1].clay=28.0;
		cls[2].sand=10.0;
		cls[2].clay=27.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=50.0\n");
			hf=50.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=10.0;
		cls[0].clay=14.0;
		cls[1].sand=20.0;
		cls[1].clay=28.0;
		cls[2].sand=10.0;
		cls[2].clay=27.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=50.0\n");
			hf=50.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=14.0;
		cls[0].clay=30.0;
		cls[1].sand=20.0;
		cls[1].clay=28.0;
		cls[2].sand=10.0;
		cls[2].clay=27.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=50.0\n");
			hf=50.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=14.0;
		cls[0].clay=30.0;
		cls[1].sand=20.0;
		cls[1].clay=28.0;
		cls[2].sand=16.0;
		cls[2].clay=35.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=50.0\n");
			hf=50.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=23.0;
		cls[0].clay=42.0;
		cls[1].sand=20.0;
		cls[1].clay=28.0;
		cls[2].sand=16.0;
		cls[2].clay=35.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=50.0\n");
			hf=50.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=23.0;
		cls[0].clay=42.0;
		cls[1].sand=20.0;
		cls[1].clay=28.0;
		cls[2].sand=35.0;
		cls[2].clay=42.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=50.0\n");
			hf=50.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=23.0;
		cls[0].clay=42.0;
		cls[1].sand=36.0;
		cls[1].clay=46.0;
		cls[2].sand=35.0;
		cls[2].clay=42.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=50.0\n");
			hf=50.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=50.0;
		cls[0].clay=50.0;
		cls[1].sand=36.0;
		cls[1].clay=46.0;
		cls[2].sand=35.0;
		cls[2].clay=42.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=50.0\n");
			hf=50.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=50.0;
		cls[0].clay=50.0;
		cls[1].sand=36.0;
		cls[1].clay=46.0;
		cls[2].sand=45.0;
		cls[2].clay=55.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=50.0\n");
			hf=50.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=38.0;
		cls[0].clay=55.0;
		cls[1].sand=36.0;
		cls[1].clay=46.0;
		cls[2].sand=45.0;
		cls[2].clay=55.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=80.0\n");
			hf=80.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=38.0;
		cls[0].clay=55.0;
		cls[1].sand=42.0;
		cls[1].clay=58.0;
		cls[2].sand=45.0;
		cls[2].clay=55.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=80.0\n");
			hf=80.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=38.0;
		cls[0].clay=55.0;
		cls[1].sand=36.0;
		cls[1].clay=46.0;
		cls[2].sand=23.0;
		cls[2].clay=42.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=80.0\n");
			hf=80.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=38.0;
		cls[0].clay=55.0;
		cls[1].sand=0.0;
		cls[1].clay=44.0;
		cls[2].sand=23.0;
		cls[2].clay=42.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=80.0\n");
			hf=80.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=16.0;
		cls[0].clay=35.0;
		cls[1].sand=0.0;
		cls[1].clay=44.0;
		cls[2].sand=23.0;
		cls[2].clay=42.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=80.0\n");
			hf=80.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=16.0;
		cls[0].clay=35.0;
		cls[1].sand=0.0;
		cls[1].clay=44.0;
		cls[2].sand=14.0;
		cls[2].clay=30.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=80.0\n");
			hf=80.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=10.0;
		cls[0].clay=27.0;
		cls[1].sand=0.0;
		cls[1].clay=44.0;
		cls[2].sand=14.0;
		cls[2].clay=30.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=80.0\n");
			hf=80.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=10.0;
		cls[0].clay=27.0;
		cls[1].sand=0.0;
		cls[1].clay=44.0;
		cls[2].sand=0.0;
		cls[2].clay=28.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=80.0\n");
			hf=80.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=17.0;
		cls[0].clay=55.0;
		cls[1].sand=0.0;
		cls[1].clay=44.0;
		cls[2].sand=0.0;
		cls[2].clay=54.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=125.0\n");
			hf=125.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=17.0;
		cls[0].clay=55.0;
		cls[1].sand=0.0;
		cls[1].clay=44.0;
		cls[2].sand=38.0;
		cls[2].clay=55.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=125.0\n");
			hf=125.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=17.0;
		cls[0].clay=55.0;
		cls[1].sand=30.0;
		cls[1].clay=60.0;
		cls[2].sand=38.0;
		cls[2].clay=55.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=125.0\n");
			hf=125.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=42.0;
		cls[0].clay=58.0;
		cls[1].sand=30.0;
		cls[1].clay=60.0;
		cls[2].sand=38.0;
		cls[2].clay=55.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=125.0\n");
			hf=125.0;
		}
	}
	if (index==0){// if index not found then continue
		cls[0].sand=42.0;
		cls[0].clay=58.0;
		cls[1].sand=30.0;
		cls[1].clay=60.0;
		cls[2].sand=34.0;
		cls[2].clay=66.0;
		mark[0]=point_in_triangle(sand_input,clay_input,silt_input,cls[0].sand,cls[0].clay,cls[0].silt,cls[1].sand,cls[1].clay,cls[1].silt,cls[2].sand,cls[2].clay,cls[2].silt);
		if(mark[0]==1){
			index=1;
			//printf("hf=125.0\n");
			hf=125.0;
		}
	}
	return hf;
}
