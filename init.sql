-- (c) 2010 by Anton Korenyushkin


DELETE FROM ak.meta WHERE schema_name = 'public';


CREATE FUNCTION ak.drop_schema(name text) RETURNS void AS $$
BEGIN
    DELETE FROM ak.meta WHERE schema_name = name;
    EXECUTE 'DROP SCHEMA ' || quote_ident(name) || ' CASCADE';
END
$$ LANGUAGE plpgsql VOLATILE;


CREATE FUNCTION ak.drop_schemas(prefix text) RETURNS void AS $$
DECLARE
    cmd text;
    name text;
BEGIN
    FOR name IN
        DELETE FROM ak.meta
        WHERE schema_name = prefix
        OR schema_name LIKE prefix || ':%'
        RETURNING *
    LOOP
        cmd := cmd || ',' || quote_ident(name);
        EXECUTE 'DROP SCHEMA ' || quote_ident(name) || ' CASCADE';
    END LOOP;
END
$$ LANGUAGE plpgsql VOLATILE;


CREATE FUNCTION ak.rename_schema(name text, new_name text) RETURNS void AS $$
BEGIN
    EXECUTE 'ALTER SCHEMA ' || quote_ident(name) ||
            ' RENAME TO ' || quote_ident(new_name);
    UPDATE ak.meta
    SET schema_name = new_name
    WHERE schema_name = name;
END
$$ LANGUAGE plpgsql VOLATILE;


CREATE FUNCTION ak.drop_all_schemas() RETURNS void AS $$
DECLARE
    name text;
BEGIN
    FOR name IN DELETE FROM ak.meta RETURNING *
    LOOP
        EXECUTE 'DROP SCHEMA ' || quote_ident(name) || ' CASCADE';
    END LOOP;
END
$$ LANGUAGE plpgsql VOLATILE;


CREATE FUNCTION ak.rename_dev(name text, new_name text) RETURNS void AS $$
DECLARE
    schema_name text;
BEGIN
    EXECUTE 'ALTER TABLESPACE ' || quote_ident(name) ||
            ' RENAME TO ' || quote_ident(new_name);
    FOR schema_name IN
        SELECT ak.meta.schema_name
        FROM ak.meta
        WHERE ak.meta.schema_name LIKE name || ':%'
    LOOP
        PERFORM ak.rename_schema(
            schema_name,
            new_name || substring(schema_name from char_length(name) + 1));
    END LOOP;
END
$$ LANGUAGE plpgsql VOLATILE;
