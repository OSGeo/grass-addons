project(r.futures.demand LANGUAGES NONE)

include(build_addon)

build_addon(
  ${PROJECT_NAME}
  SOURCES ${PROJECT_NAME}.py
  DOCFILES
    r_futures_demand_plot_exp_approach.png
    r_futures_demand_plot_exponential.png
    r_futures_demand_plot_linear.png
    r_futures_demand_plot_logarithmic.png
    r_futures_demand_plot_logarithmic2.png
    ${PROJECT_NAME}.html
    ${PROJECT_NAME}.md)
