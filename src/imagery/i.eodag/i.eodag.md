## DESCRIPTION

### WARNING: I.EODAG IS UNDER DEVELOPMENT. THIS IS AN EXPERIMENTAL VERSION

*i.eodag* allows to search and download imagery scenes, e.g. Sentinel,
Landsat, and MODIS, as well as other Earth Observation products, from a
number of different providers. The module utilizes the [EODAG
API](https://eodag.readthedocs.io/en/stable/), as a single interface to
search for products within the supported providers.

By default *i.eodag* will search for products which footprint intersects
the current computational region extent. Users can alternatively opt to
pass a vector map throught the **map** option to define the area of
interest (AOI) and change the relation with product footprints by means
of the **area\_relation** or **minimum\_overlap** options.

To only list available scenes, **l** flag must be set. If no **start**
or **end** dates are provided, the module will search scenes from the
past 60 days. Note that the dates used for searching **start**, **end**,
in addition to **ingestiondate**, which is displayed when listing found
scenes, refer to the sensing time of the scene.

To download all scenes found within the time frame provided, users must
remove the **l** flag and provide an **output** directory. Otherwise,
files will be downloaded into the /tmp directory. To download only
selected scenes, one or more IDs must be provided through the **id**
option.

To be able to download data through *i.eodag*, users will need to
register for the providers of interest. *i.eodag* reads user credentials
from the EODAG YAML config file. Users have to specify the configuration
file path through the **config** option, otherwise *i.eodag* will use
the credentials found in the default config file which is auto-generated
the first time EODAG is used after installation. The configuration file
is stored by default in `$HOME/.config/eodag/eodag.yml`.

### Use Cases

There are different ways to use *i.eodag*:

#### Searching from scratch

When users are searching for scenes for the first time and they don't
know the IDs of specific scenes. The searching is done by setting the
main options e.g. **producttype**, **start**, **end**, **clouds** and,
possibly, **provider**.

#### Searching using scenes IDs

Users have a set of scenes IDs that they want to search for and
download. They can either use the **id** option or use the **file**
option and pass a text file, with one ID per line. When searching with
ID, users must specify the product type that the IDs belong to.
Specifying a provider is not mandatory, but it is recommended. In case
users do not specify the provider, each scene might be offered from a
different provider. Note that all scenes IDs have to belong to the same
product type.

#### Reading products from a GeoJSON file

When the user has already performed a first search and saved the results
into a GeoJSON file using the **save** option. Users will then pass the
GeoJSON file through the **file** option. No additional searching will
be done in this case, but users will be able to further filter the
products saved in the GeoJSON file through the different options, e.g.
**start, end, query, area\_relation, etc.**

## NOTES

### Querying

Querying, aka. filtering, is a method introduced to *i.eodag* to further
filter the search results based on an extended list of products'
properties, called
[queryables](https://eodag.readthedocs.io/en/stable/notebooks/api_user_guide/4_search.html#Queryables).
The **print** option can be used to get hints of the avaible queryables.
For example, to get the queryables for the product "S2\_MSI\_L2A" that
is offered by Copernicus Data Space Ecosystem (cop\_dataspace):

```sh
i.eodag print=queryables provider=cop_dataspace producttype=S2_MSI_L2A
```

Note that the **print** option only gives a subset of the avaible
queryables, and users can in fact use any of the product's properties
for filtering. If users are not sure about the all the available
properties for a product, they can run a generic search with the **j**
flag and **limit=1**, to see an instance of the product of interest. The
available queryables will be found in the JSON output within the
"properties" section.

The possible types of these properties are:

- **str** most common type.
- **int** may have a specified range.
- **float** may have a specified range.
- **Literal** has a list of options to choose from.

The **query** option is used for querying. There is a list of rules that
users need to follow when composing queries:

#### Operators

| Relation              | Operator |
| --------------------- | :------: |
| Equal                 |   `eq`   |
| Not Equal             |   `ne`   |
| Less Than or Equal    |   `le`   |
| Less Than             |   `lt`   |
| Greater Than or Equal |   `ge`   |
| Greater Than          |   `gt`   |

#### Query Structure

Basic structure:

```sh
{queryable} = {value} ; {operator}
```

Example

Print products which **orbitDirection** property is "DESCENDING":

```sh
i.eodag -l start=2022-05-01 end=2022-06-01 \
provider=cop_dataspace producttype=S2_MSI_L2A \
query="orbitDirection=DESCENDING;eq"
```

NOTE: If no operator is specified then the 'eq' opeartor will be used.

Multiple values per queryable:

```sh
{queryable} = {value_1} ; {operator_1} | {value_2} ; {opeartor_2}
```

Examples

Print products which **cloudCover** is either less than 30 **OR**
greater than 60, aka. \[0, 30) ∪ (60, 100\].  
Notice here that multiple values are used to indicate the **OR**
relation.

```sh
i.eodag -l start=2022-05-01 end=2022-06-01 \
provider=cop_dataspace producttype=S2_MSI_L2A \
query="cloudCover=30;lt | 60;gt"
```

To use the **AND** relation instead, write them in separate queries.  
Print products which **cloudCover** is greater than 30 **AND** less than
60, aka. (30, 60).

```sh
i.eodag -l start=2022-05-01 end=2022-06-01 \
provider=cop_dataspace producttype=S2_MSI_L2A \
query="cloudCover=30;gt, cloudCover=60;lt"
```

Print products which **cloudCover** is greater than 30 **AND** less than
60, and having a descending orbit.

```sh
i.eodag -l start=2022-05-01 end=2022-06-01 \
provider=cop_dataspace producttype=S2_MSI_L2A \
query="cloudCover=30;gt, cloudCover=60;lt, orbitDirection=DESCENDING"
```

Null Values

In some cases, products might have **Null** as the value of some
properties (aka. queryables). These products will be filtered out by
default. In case users do not want them to be filtered out, they need to
provide an additional **Null** value to the queryable.

Examples

Print products which **orbitDirection** is **DESCENDING**.

```sh
i.eodag -l start=2022-05-01 end=2022-06-01 \
provider=cop_dataspace producttype=S2_MSI_L2A \
query="orbitDirection=DESCENDING"
```

Print products which **orbitDirection** is **DESCENDING OR Null**.

```sh
i.eodag -l start=2022-05-01 end=2022-06-01 \
provider=cop_dataspace producttype=S2_MSI_L2A \
query="orbitDirection=DESCENDING|Null"
```

#### Frequently used queryables

- **cloudCover** range \[0, 100\]
- **orbitNumber**
- **orbitDirection**
- **storageStatus**
- **start** ISO formated date referring to products caputred on start
    date or later.
- **end** ISO formated date referring to products caputred on end date
    or earlier.

NOTE: These queryables are only for reference, and they might not always
be avaiable for all providers/products.

### EODAG configuration

EODAG configuration **YAML** file is used to set multiple values,
including:

- **Priority**  
    Used when the *i.eodag* tries to search for a product, with no
    **provider** specified. Searching is attempted with providers with
    higher priority first.

- **Credentials**  
    Some providers require credentials to conduct searching, while
    others do not. However, users will need to set the credentials for
    downloading, in most cases. See [Providers
    Registration](https://eodag.readthedocs.io/en/stable/getting_started_guide/register.html)
    for more details about registration and credentials.

    NOTE: If users notice that *i.eodag* doesn't recognize a specific
    provider when searching or downloading, it might be that they need
    to specify the credentials for that provider.

- **Output Prefix**  
    Setting the output\_prefix is similar to using the **output**
    option. It is the directory into which downloaded products will be
    saved.

Following is an example for a config YAML file with Copernicus Dataspace
credentials:

```sh
cop_dataspace:
    priority: # Lower value means lower priority (Default: 0)
    search:   # Search parameters configuration
    download:
        extract:
        outputs_prefix:
    auth:
        credentials:
          username: email@email.com
          password: password
```

#### Creodias

To register to Creodias, users should create an account
[here](https://portal.creodias.eu/register.php), and then use their
username and password in the eodag configuration file. Users will also
need TOTP, a 6-digits temporary one time password, to be able to
authenticate and download scenes (product search within creodias can be
done without registering). This TOTP is only valid for very short time,
i.e., 30 to 60 seconds, so it shall not be set through the eodag
configuration file. When *i.eodag* attempts to download a scene from
creodias, users will be prompted to input the TOTP. If they prefer to
discard these scenes, they should enter **"-"** instead. Note that
interactive prompt does not work in the graphical user interface.

See [Configure
EODAG](https://eodag.readthedocs.io/en/stable/getting_started_guide/configure.html)
section for more details about configuration of the providers'
credentials and other EODAG YAML config file parameters.

## EXAMPLES

Search and list the available Sentinel 2 scenes in the Copernicus Data
Space Ecosystem, using a vector map as an AOI:

```sh
v.extract input=urbanarea where="NAME = 'Durham'" output=durham

i.eodag -l start=2022-05-01 end=2022-06-01 \
    map=durham producttype=S2_MSI_L2A provider=cop_dataspace
```

Search and list the available Sentinel 2 scenes in the Copernicus Data
Space Ecosystem, with at least 70% of the AOI covered:

```sh
i.eodag -l start=2022-05-01 end=2022-06-01 \
    producttype=S2_MSI_L2A provider=cop_dataspace \
    clouds=50 map=durham minimum_overlap=70
```

Sort results descendingly by **cloudcover**, and then by
**ingestiondate**. Note that sorting with **cloudcover** uses unrounded
values, while they are rounded to the nearest integer when listing.

```sh
i.eodag -l start=2022-05-25 end=2022-06-01 \
    producttype=S2_MSI_L2A provider=cop_dataspace \
    sort=cloudcover,ingestiondate order=desc
```

Search for scenes with a list of IDs, and filter the results with the
provided parameters:

```sh
i.eodag -l file=ids_list.txt \
    start=2022-05-25 \
    area_relation=Contains clouds=3
```

Search and list the available Sentinel 2 scenes in the Copernicus Data
Space Ecosystem, with relative orbit number 54:

```sh
i.eodag -l producttype=S2_MSI_L2A \
    provider=cop_dataspace save=search_result.geojson \
    query="relativeOrbitNumber=54"
```

Search and list the available Tier 1 Landsat 9 Collection 2 Level 2
scenes in USGS, using filtering with a regular expression:

```sh
i.eodag -l producttype=LANDSAT_C2L2 \
    provider=usgs save=search_result.geojson \
    pattern="LC09.*T1"
```

Search and list Sentinel 2 scenes using IDs from Copernicus Data Space
Ecosystem:  
To download the selected scenes, simply remove the l flag.

```sh
i.eodag -l provider=cop_dataspace producttype=S2_MSI_L2A \
    id="S2A_MSIL2A_20240728T154941_N0511_R054_T17SPV_20240728T235651,
    S2A_MSIL2A_20240618T154941_N0510_R054_T17SPV_20240618T222157"
```

Search and list for a Landsat scene using its ID from USGS:  
To download the selected scene, remove the l flag.

```sh
i.eodag -l provider=usgs producttype=LANDSAT_C2L2 \
    id=LC08_L2SP_016035_20240715_20240722_02_T1
```

Download all available scenes with cloud coverage not exceeding 50% in
the /tmp directory:

```sh
i.eodag start=2022-05-25 end=2022-06-01 \
    producttype=S2_MSI_L2A provider=cop_dataspace clouds=50
```

Download only selected scenes from a text file with IDs, using the
Copernicus Data Space Ecosystem as the provider:

```sh
i.eodag file=ids_list.txt provider=cop_dataspace
```

Download only selected scenes into the *download\_here* directory, using
a custom config file:

```sh
i.eodag provider=cop_dataspace \
    id="S2B_MSIL2A_20240526T080609_N0510_R078_T37SDD_20240526T094753,
    S2B_MSIL2A_20240529T081609_N0510_R121_T37SED_20240529T124818" \
    producttype=S2_MSI_L2A \
    config=full/path/to/eodag/config.yaml \
    output=download_here
```

List recognized EODAG providers:

```sh
i.eodag print=providers
```

List recognized EODAG providers offering Sentinel 2 scenes:

```sh
i.eodag print=providers producttype=S2_MSI_L2A
```

List recognized EODAG products:

```sh
i.eodag print=products
```

List recognized EODAG products offered by Copernicus Data Space
Ecosystem:

```sh
i.eodag print=products provider=cop_dataspace
```

List queryables for Sentinel 2 scenes offered by Copernicus Data Space
Ecosystem:

```sh
i.eodag print=queryables provider=cop_dataspace producttype=S2_MSI_L2A
```

List current EODAG configuration:

```sh
i.eodag print=config
```

List current EODAG configuration for Copernicus Data Space Ecosystem:

```sh
i.eodag print=config provider=cop_dataspace
```

Print query summary:

```sh
i.eodag -lp provider=usgs producttype=LANDSAT_C2L2 area_relation=IsWithin clouds=30
```

## REQUIREMENTS

- [EODAG
    library](https://eodag.readthedocs.io/en/stable/getting_started_guide/install.html)
    (install with `pip install eodag`)
- For EODAG 3.0.0 and later, some of the providers have additonal
    dependencies that needs to be installed, e.g. `pip install
    eodag[usgs]`, for more info see [installation
    page](https://eodag.readthedocs.io/en/stable/getting_started_guide/install.html).
    To install all dependencies use `pip install eodag[all]`

## SEE ALSO

*[i.landsat](i.landsat.md), [i.sentinel](i.sentinel.md),
[i.modis](i.modis.md)*

## AUTHOR

[Hamed Elgizery](https://github.com/HamedElgizery), Giza, Egypt.  

GSoC 2024 Mentors: Luca Delucchi, Stefan Blumentrath, Veronica Andreo
