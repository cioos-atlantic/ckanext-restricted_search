# ckanext-restricted_search

**TODO:** Put a description of your extension here:  What does it do? What features does it have? Consider including some screenshots or embedding a video!


## Changes

The plugin alters the filter query ('fq') in the dataset search by attaching an additional filter to the data.

The plugin interacts with the following templates and may override or be overridden by any using the following blocks.

    scheming/package/read.html
        block package_tags
        block package_notes
    snippets/package_item.html
        block heading_private
    snippets/search_form.html
        block search_facets
        block search_sortby

It also provides a alternate cioos_siooc_schema.json that adds two new fields:
    extras_eov_restricted and extras_keywords_restricted
The fields are direct copies of the 'eov' and 'keywords' fields in the original schema except with the field_name and label updated to match the new field name and 'required' set to false

Should any changes be made to the original cioos_siooc_schema.json the schema in this plugin should be updated to match. The two new fields can be copied into the new schema under the 'eov' section, unless the 'keywords' or 'eov' sections have changed. In that case copy the new changes into two new fields and follow the instructions detailed in the paragraph above.

Found here : https://github.com/cioos-siooc/cioos-siooc-schema/blob/master/cioos-siooc_schema.json 

The plugin also enables CKAN to process XMLs with keywords tagged as restricted. 

See the page here for more details: https://github.com/cioos-atlantic/restricted_search/wiki/Metadata

## Requirements

This plugin is compatible with CKAN 2.9 or later

Requires the following extensions:

    ckanext-scheming
    ckanext-spatial

## Installation

To install ckanext-restricted_search:

1. Activate your CKAN virtual environment, for example:

     . /usr/lib/ckan/default/bin/activate

2. Clone the source and install it on the virtualenv

    git clone https://github.com/JaredMcLellan/ckanext-restricted_search.git
    cd ckanext-restricted_search
    pip install -e .
	pip install -r requirements.txt
    python setup.py develop

3. Add the three plugin files to the `ckan.plugins` setting in your CKAN
   config file (by default the config file is located at
   `/etc/ckan/default/ckan.ini`). `restricted_search` should go before any
   other plugins that affect templates or themes. `restricted_harvest` and 
   `restricted_harvest_validator` should be placed after any other 
   harvester plugins.

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu:

     sudo service apache2 reload
     
5. If running separately, you may also have to restart the CKAN harvesters


## Config settings

If using ckanext-scheming plugins such as scheming_datasets or scheming_organizations, place restricted_search above those plugins in the config file.

If using the CIOOS schema, set the dataset scheming in the config file to use the one provided by the plugin:

    scheming.dataset_schemas = ckanext.scheming:cioos_siooc_schema.json


## Developer installation

To install ckanext-restricted_search for development, activate your CKAN virtualenv and
do:

    git clone https://github.com/JaredMcLellan/ckanext-restricted_search.git
    cd ckanext-restricted_search
    python setup.py develop
    pip install -r dev-requirements.txt


## Tests

To run the tests, do:

    pytest --ckan-ini=test.ini


## Releasing a new version of ckanext-restricted_search

If ckanext-restricted_search should be available on PyPI you can follow these steps to publish a new version:

1. Update the version number in the `setup.py` file. See [PEP 440](http://legacy.python.org/dev/peps/pep-0440/#public-version-identifiers) for how to choose version numbers.

2. Make sure you have the latest version of necessary packages:

    pip install --upgrade setuptools wheel twine

3. Create a source and binary distributions of the new version:

       python setup.py sdist bdist_wheel && twine check dist/*

   Fix any errors you get.

4. Upload the source distribution to PyPI:

       twine upload dist/*

5. Commit any outstanding changes:

       git commit -a
       git push

6. Tag the new release of the project on GitHub with the version number from
   the `setup.py` file. For example if the version number in `setup.py` is
   0.0.1 then do:

       git tag 0.0.1
       git push --tags

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
