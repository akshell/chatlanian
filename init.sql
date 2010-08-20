-- (c) 2010 by Anton Korenyushkin


CREATE FUNCTION ak.drop_schemas(main_schema_name text) RETURNS void AS $$
DECLARE
    cmd text;
    schema_name name;
BEGIN
    cmd := 'DROP SCHEMA ' || quote_ident(main_schema_name);
    FOR schema_name IN
        SELECT nspname
        FROM pg_catalog.pg_namespace
        WHERE nspname LIKE main_schema_name || ':%'
    LOOP
        cmd := cmd || ',' || quote_ident(schema_name);
    END LOOP;
    EXECUTE cmd || ' CASCADE';
END
$$ LANGUAGE plpgsql VOLATILE;
