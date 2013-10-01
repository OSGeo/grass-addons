#!/usr/bin/env python
#
############################################################################
#
# MODULE:		Set of time discrete population models in fisheries science
#
# AUTHOR(S):		Johannes Radinger
#				
# VERSION:		
#
# DATE:			2013-08-28
#
#############################################################################
#%Module
#% description: Set of population models (fisheries science)
#% keywords: Population growth model
#%End
#%option
#% key: n_initial
#% type: string
#% gisprompt: old,cell,raster
#% description: Map with number of individuals per cell at time t0 (initial population size)
#% required: yes
#%end
#%option
#% key: timesteps
#% type: integer
#% description: Number of time steps
#% required: yes
#% answer: 1
#%end
#%Option
#% key: exponential_output
#% type: string
#% gisprompt: new,cell,raster
#% required: no
#% multiple: no
#% key_desc: name
#% description: Name for exponential model output map
#% guisection: Exponential
#%end
#%option
#% key: r_exp_fix
#% type: double
#% description: Fixed value of intrinsic rate of increase, log(finite rate of increase, lambda)
#% required: no
#% multiple: no
#% guisection: Exponential
#%end
#%option
#% key: r_exp_map
#% type: string
#% gisprompt: old,cell,raster
#% description: Map with intrinsic rate of increase, log(finite rate of increase, lambda)
#% required: no
#% multiple: no
#% guisection: Exponential
#%end
#%Option
#% key: ricker_output
#% type: string
#% gisprompt: new,cell,raster
#% required: no
#% multiple: no
#% key_desc: name
#% description: Name for Ricker model output map
#% guisection: Ricker
#%end
#%option
#% key: k_fix
#% type: integer
#% description: Fixed value of carrying capacity of the environment
#% required: no
#% guisection: Ricker
#%end
#%option
#% key: k_map
#% type: string
#% gisprompt: old,cell,raster
#% description: Map with carrying capacity of the environment
#% required: no
#% guisection: Ricker
#%end
#%option
#% key: r_rick_fix
#% type: double
#% description: Fixed value of intrinsic rate of increase (Ricker)
#% required: no
#% multiple: no
#% guisection: Ricker
#%end
#%option
#% key: r_rick_map
#% gisprompt: old,cell,raster
#% description: Map with intrinsic rate of increase (Ricker)
#% required: no
#% multiple: no
#% guisection: Ricker
#%end
#%Option
#% key: seed
#% type: integer
#% required: no
#% multiple: no
#% description: fixed seed for random rounding
#% guisection: Optional
#%End
#%Flag
#% key: i
#% description: Calculate models with rounded integer values
#%end



# import required base modules
import sys
import os
import atexit
import math #for function sqrt()

# import required grass modules
import grass.script as grass
import grass.script.array as garray



# import required numpy/scipy modules
import numpy



def cleanup():
	grass.message(_("This is the cleanup part"))


def main():
	############ DEFINITION CLEANUP TEMPORARY FILES ##############
	#global variables for cleanup
	global tmp_map_rast
	global tmp_map_vect

	tmp_map_rast = []
	tmp_map_vect = []


	############ PARAMETER INPUT ##############
	# Check for correct input
	if (str(options['exponential_output']) == '' and str(options['ricker_output']) == ''):
		grass.fatal(_("Output name for a model is missing"))
	

	#Model parameters input
	t = int(options['timesteps'])
	

	# Customized rounding function. Round based on a probability (p=digits after decimal point) to avoid "local stable states"
	def prob_round(x, prec = 0):
    		fixup = numpy.sign(x) * 10**prec
    		x *= fixup
		if options['seed']:
			numpy.random.seed(seed=int(options['seed'])) 
    		round_func = int(x) + numpy.random.binomial(1,x-int(x))
    		return round_func/fixup
	vprob_round = numpy.vectorize(prob_round)


	################# Model Definiations #################
	# Model definitions modified from R scripts (http://www.mbr-pwrc.usgs.gov/workshops/unmarked/Rscripts/script-state-space.R)
	# Exponential Model
	def exponential_mod(n0,r,t):
		n = n0
		for t in range(t):
			n = 1.0*n*numpy.exp(r)
			if flags['i']:
				n = vprob_round(n)
		return 	n

	# Ricker Model
	def ricker_mod(n0,r,k,t):
		n = n0
		for t in range(t):
			n = 1.0*n*numpy.exp(r*(1-(n/k)))
			if flags['i']:
				n = vprob_round(n)
		return 	n
	vricker_mod = numpy.vectorize(ricker_mod)
	
	################# Exponential Model #################
	if options['exponential_output']:
		# Check for correct input
		if (options['r_exp_fix'] and options['r_exp_map']):
			grass.fatal(_("Provide either fixed value for r or raster map"))

		# Define r
		if options['r_exp_map']:
			grass.message(_("r_exp_map provided"))
			r = garray.array()
			r.read(options['r_exp_map'])
		elif options['r_exp_fix']:
			r = float(options['r_exp_fix'])
		else:
			grass.fatal(_("No r value/map provided for exponential model"))
		n0_map = garray.array()
		n0_map.read(options['n_initial'])
		exponential_map = garray.array()
		exponential_map[...] = exponential_mod(n0_map,r,t)
		exponential_map.write(options['exponential_output'])


	################# Ricker Model #################
	if options['ricker_output']:
		# Check for correct input
		if (options['r_rick_fix'] and options['r_rick_map']):
			grass.fatal(_("Provide either fixed value for r or raster map"))
		if (options['k_fix'] and options['k_map']):
			grass.fatal(_("Provide either fixed value for carrying capacity (K) or raster map"))

		# Define r
		if options['r_rick_map']:
			r = garray.array()
			r.read(options['r_rick_map'])
		elif options['r_rick_fix']:
			r = float(options['r_rick_fix'])
		else:
			grass.fatal(_("No r value/map for Ricker model provided"))

		# Define k
		if options['k_map']:
			k = garray.array()
			k.read(options['k_map'])
		elif options['k_fix']:
			k = float(options['k_fix'])
		else:
			grass.fatal(_("No value/map for carrying capacity (k) provided"))
		n0_map = garray.array()
		n0_map.read(options['n_initial'])
		ricker_map = garray.array()
		ricker_map[...] = ricker_mod(n0_map,r,k,t)
		ricker_map.write(options['ricker_output'])



	return 0


if __name__ == "__main__":
	options, flags = grass.parser()
	atexit.register(cleanup)
	sys.exit(main())
