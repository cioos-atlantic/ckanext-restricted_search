import logging

from jmespath import search

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as helper
import ckanext.restricted_search.cli as cli

log = logging.getLogger(__name__)

class RestrictedSearchPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IFacets)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IActions, inherit=True)
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.IClick)

    
    def get_commands(self):
        return cli.get_commands()

    # IConfigurer
    # ITemplateHelpers
    def get_helpers(self):
        return {
        }

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic',
            'restricted_search')

    def get_actions(self):
        return {}

    
    """
    Required by CKAN for the schema changes to function
    """
    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return False
    
    """
    Required by CKAN for the schema changes to function
    """
    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    # Interfaces
    def dataset_facets(self, facets_dict, package_type):
        return facets_dict

    def organization_facets(self, facets_dict, organization_type, package_type, ):
        return facets_dict

    def group_facets(self, facets_dict, group_type, package_type, ):
        return facets_dict

    def before_search(self, search_params):
        log.info("before_search")
        if 'fq' not in search_params:
            return search_params
        facet_query = search_params['fq']
        if 'restricted_search:"enabled"' in facet_query:
            facet_query = facet_query.replace('restricted_search:"enabled"', "")
            if "eov:" in facet_query or 'tags_en:' in facet_query or 'tags_fr:' in facet_query or 'tags:' in facet_query:
                fq_split = facet_query.split(' ')
                final_query = ""
                for x in fq_split:
                    if(x.startswith('eov:') and '"' in x):
                        eov = x.split('"')[1]
                        eov_restricted = 'res_extras_eov_restricted:"' + eov + '"'
                        x= '(eov:"' + eov + '" OR ' + eov_restricted + ')'
                    elif(x.startswith('tags_en:') and '"' in x):
                        tags = x.split('"')[1]
                        tags_restricted = 'res_extras_keywords_restricted:"' + tags + '"'
                        x= '(tags_en:"' + tags + '" OR ' + tags_restricted + ')'
                    elif(x.startswith('tags_fr:') and '"' in x):
                        tags = x.split('"')[1]
                        tags_restricted = 'res_extras_keywords_restricted:"' + tags + '"'
                        x= '(tags_fr:"' + tags + '" OR ' + tags_restricted + ')'
                    elif(x.startswith('tags:') and '"' in x):
                        tags = x.split('"')[1]
                        tags_restricted = 'res_extras_keywords_restricted:"' + tags + '"'
                        x= '(tags:"' + tags + '" OR ' + tags_restricted + ')'
                    final_query += x + ' '
                search_params['fq'] = final_query.strip()
            else:
                search_params['fq'] = facet_query.strip()   
        log.info(search_params)
        return search_params


    def after_search(self, search_results, search_params):
        # Gets the current user's ID (or if the user object does not exist, sets user as 'public')
        log.info("After search")
        log.info(search_results['search_facets'])
        datasets = search_results['results']
        
        # Checks if the search requires restricted variable checking
        # TODO Overall costly - find a better alternative
        restricted_search_enabled = False
        restricted_search_eovs = []
        restricted_search_keywords = []
        for x in search_params['fq'][0].replace(")","").replace("(", "").split(" "):
            if(x.startswith('res_extras_eov_restricted')):
                restricted_search_eovs.append(x.split('"')[1])
                restricted_search_enabled = True
            elif(x.startswith('res_extras_keywords_restricted')):
                restricted_search_keywords.append(x.split('"')[1])
                restricted_search_enabled = True

        # Go through each of the datasets returned in the results
        for x in range(len(datasets)):
            pkg_dict = search_results['results'][x]
            if restricted_search_enabled:
                try:
                    if('res_extras_eov_restricted' in pkg_dict):
                        for x in restricted_search_eovs:
                            if x in pkg_dict['res_extras_eov_restricted']:
                                pkg_dict['mark_restricted'] = True
                                continue
                    if('res_extras_keywords_restricted' in pkg_dict and 'mark_restricted' not in pkg_dict):
                        for x in restricted_search_keywords:
                            if x in pkg_dict['res_extras_keywords_restricted']['en'] or x in pkg_dict['res_extras_keywords_restricted']['fr']:
                                pkg_dict['mark_restricted'] = True
                                continue
                except:
                    log.info('An error with restricted search occurred')
        return search_results

        
    def after_show(self,context, pkg_dict):
        if context['package'].type != 'dataset':
            return pkg_dict
        if('user' not in context):
            log.info("This is before index we're done here.")
            return pkg_dict
        log.info(pkg_dict.keys())
        return pkg_dict
    