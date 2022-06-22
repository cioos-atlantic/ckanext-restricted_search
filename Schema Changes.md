The plugin uses two variables res_extras_eov_restricted and res_extras_keyword_restricted 

#res_extras
Without changing the CIOOS SOLR schema there are a few extra fields that allow placing custom fields into the database using dynamic fields

    <dynamicField name="*_date" type="date" indexed="true" stored="true" multiValued="false"/>
    <dynamicField name="extras_*" type="text" indexed="true" stored="true" multiValued="false"/>
    <dynamicField name="res_extras_*" type="text" indexed="true" stored="true" multiValued="true"/>
    <dynamicField name="vocab_*" type="string" indexed="true" stored="true" multiValued="true"/>
    <dynamicField name="*" type="string" indexed="true"  stored="false"/>

The wildcard field is not stored and \*_date and extras_\* are not multivalued which leaves res_extras_ and vocab_ as options

res_extras was chosen as it was the choice for the extra variables as it made sense to treat them as extra resource fields
However, it is also a text field instead of string and gets tokenized, unlike the original eov and keyword fields