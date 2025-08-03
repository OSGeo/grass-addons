## DESCRIPTION

*r.gradient* create a gradient map. It is able to create horizontal,
vertical and oblique gradient.

## EXAMPLES

To calculate vertical gradient from North to South

```sh
  r.gradient output=gradient_ns range=0,50 direction=N-S
  
```

To calculate horizontal gradient from East to West

```sh
  r.gradient output=gradient_ea range=10,20 direction=E-W
  
```

To calculate oblique gradient from North-East to South-West you have to
set also the *percentile* option to set the slope of the gradient.

```sh
  r.gradient output=gradient_oblique range=10,20 direction=NE-SW
  
```

## AUTHORS

Luca Delucchi, Fondazione E. Mach (Italy)

Thanks to Johannes Radinger for the code of horizontal and vertical
gradient
