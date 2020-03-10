from .distance import compute_artificial_proximity
from .accessibility import compute_artificial_accessibility


def build_infrastructure_component(
        infrastructure,
        artificial_distance_categories,
        artificial_proximity_map_name,
        roads_distance_categories,
        roads_proximity_map_name,
        artificial_accessibility_map_name,
        artificial=None,
        roads=None,
    ):
    """
    Build and return the 'infrastructure' component
    """
    infrastructure_component = []
    infrastructure_components = []

    if infrastructure:
        infrastructure_component.append(infrastructure)

    """Artificial surfaces (including Roads)"""

    if artificial and roads:

        msg = "*** Roads distance categories: {c}"
        msg = msg.format(c=roads_distance_categories)
        grass.debug(_(msg))
        roads_proximity = compute_artificial_proximity(
            raster=roads,
            distance_categories=roads_distance_categories,
            output_name=roads_proximity_map_name,
        )

        msg = "*** Artificial distance categories: {c}"
        msg = msg.format(c=artificial_distance_categories)
        grass.debug(_(msg))
        artificial_proximity = compute_artificial_proximity(
            raster=artificial,
            distance_categories=artificial_distance_categories,
            output_name=artificial_proximity_map_name,
        )

        artificial_accessibility = compute_artificial_accessibility(
            artificial_proximity,
            roads_proximity,
            output_name=artificial_accessibility_map_name,
        )

        infrastructure_components.append(artificial_accessibility)

    # merge infrastructure component related maps in one list
    infrastructure_component += infrastructure_components
    return infrastructure_component
