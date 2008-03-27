// Broadband albedo Aster 

double bb_alb_aster( double greenchan, double redchan, double nirchan, double swirchan1, double swirchan2, double swirchan3, double swirchan4, double swirchan5, double swirchan6 )
{
	double	result;
	
	result = ( 0.09*greenchan + 0.06*redchan + 0.1*nirchan + 0.092*swirchan1 + 0.035*swirchan2 + 0.04*swirchan3 + 0.047*swirchan4 + 0.07*swirchan5 + 0.068*swirchan6 ) / ((0.09+0.06+0.1+0.092+0.035+0.04+0.047+0.07+0.068)*1000.0);

	return result;
}

