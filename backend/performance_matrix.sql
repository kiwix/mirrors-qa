-- All variables and parameters are prefixed with v_ where necessary to
-- avoid ambiguity with a table name or a column of the same name.

-- Get a mirror by id
DROP FUNCTION IF EXISTS get_mirror_by_id;
CREATE OR REPLACE FUNCTION get_mirror_by_id(v_mirror_id varchar)
RETURNS mirror
AS
$$
DECLARE
    result mirror;
BEGIN
    SELECT * INTO result
    FROM mirror WHERE mirror.id = v_mirror_id;

    -- Postgresql keeps track of the result in the global variable 'found'
    IF NOT found THEN
	raise exception 'mirror % not found', v_mirror_id;
    END IF;

    RETURN result;
END;
$$
LANGUAGE plpgsql;


-- Get a country by code
DROP FUNCTION IF EXISTS get_country_by_code;
CREATE OR REPLACE FUNCTION get_country_by_code(v_country_code varchar)
RETURNS country
AS
$$
DECLARE
    result country;
BEGIN
    SELECT * INTO result
    FROM country WHERE country.code = v_country_code;

    IF NOT found THEN
	raise exception 'country % not found', v_country_code;
    END IF;

    RETURN result;
END;
$$
LANGUAGE plpgsql;


-- Get a region by code
DROP FUNCTION IF EXISTS get_region_by_code;
CREATE OR REPLACE FUNCTION get_region_by_code(v_region_code varchar)
RETURNS region
AS
$$
DECLARE
    result region;
BEGIN
    SELECT * INTO result
    FROM region WHERE region.code = v_region_code;

    IF NOT found THEN
	raise exception 'region % not found', v_region_code;
    END IF;

    RETURN result;
END;
$$
LANGUAGE plpgsql;


-- Get all the tests for a specific country at a specific mirror.
DROP FUNCTION IF EXISTS get_all_tests_for_country;
CREATE OR REPLACE FUNCTION get_all_tests_for_country (
    v_mirror_id varchar,
    v_country_code varchar,
    start_date date,
    end_date date
)
RETURNS SETOF test
AS
$$
DECLARE
    v_mirror mirror%rowtype;
BEGIN
    v_mirror := get_mirror_by_id(v_mirror_id);
    RETURN QUERY
	SELECT * FROM test
	WHERE country_code = v_country_code
	    AND status = 'SUCCEEDED'
	    AND mirror_url = v_mirror.base_url
	    AND (started_on::date BETWEEN start_date AND end_date);
END;
$$
LANGUAGE plpgsql;


-- Get all the tests for a specific region at a specific mirror.
DROP FUNCTION IF EXISTS get_all_tests_for_region;
CREATE OR REPLACE FUNCTION get_all_tests_for_region (
    v_mirror_id varchar,
    v_region_code varchar,
    start_date date,
    end_date date
)
RETURNS SETOF test
AS
$$
DECLARE
    v_mirror mirror%rowtype;
BEGIN
    v_mirror := get_mirror_by_id(v_mirror_id);
    RETURN QUERY
	SELECT * FROM test
	WHERE status = 'SUCCEEDED'
	    AND mirror_url = v_mirror.base_url
	    AND (started_on::date BETWEEN start_date AND end_date)
	    AND country_code IN (
		SELECT code FROM country WHERE country.region_code = v_region_code
	    );
END;
$$
LANGUAGE plpgsql;


-- Get all the enabled mirrors located in a country
DROP FUNCTION IF EXISTS get_enabled_mirrors_in_country;
CREATE OR REPLACE FUNCTION get_enabled_mirrors_in_country (v_country_code varchar)
RETURNS SETOF mirror
AS
$$
BEGIN
    RETURN QUERY
	SELECT * FROM mirror
	WHERE country_code = v_country_code AND enabled = 'true';
END;
$$
LANGUAGE plpgsql;


-- Get all the enabled mirrors located in a region
DROP FUNCTION IF EXISTS get_enabled_mirrors_in_region;
CREATE OR REPLACE FUNCTION get_enabled_mirrors_in_region (v_region_code varchar)
RETURNS SETOF mirror
AS
$$
BEGIN
    RETURN QUERY
	SELECT * FROM mirror
	WHERE region_code = v_region_code AND enabled = 'true';
END;
$$
LANGUAGE plpgsql;


-- Determine if a mirror serves content to a country
DROP FUNCTION IF EXISTS is_mirror_serving_country;
CREATE OR REPLACE FUNCTION is_mirror_serving_country (v_mirror mirror, v_country_code varchar)
RETURNS BOOLEAN
AS
$$
DECLARE
    -- the region_code which the country belongs to
    v_region_code varchar;
BEGIN
    -- initialize the variable for the region code of the country
    SELECT region_code
    INTO v_region_code
    FROM country
    WHERE code = v_country_code;

    -- Exclude mirrors serving a single country not this one
    IF v_mirror.country_only AND v_mirror.country_code != v_country_code THEN
        RETURN FALSE;
    END IF;

    -- Exclude mirrors serving a single region if not the region of the country
    IF v_mirror.region_only AND v_mirror.region_code != v_region_code THEN
        RETURN FALSE;
    END IF;

    -- Exclude mirrors serving other countries if country not in the list
    IF array_length(coalesce(v_mirror.other_countries, '{}'), 1) > 0
	AND v_country_code != ALL(v_mirror.other_countries)
    THEN
        RETURN FALSE;
    END IF;


    RETURN TRUE;
END;
$$
LANGUAGE plpgsql;


-- Get enabled mirrors serving content to a country
DROP FUNCTION IF EXISTS get_enabled_mirrors_serving_country;
CREATE OR REPLACE FUNCTION get_enabled_mirrors_serving_country (v_country_code varchar)
RETURNS SETOF mirror
AS
$$
BEGIN
    RETURN QUERY
	SELECT * FROM mirror m
	WHERE enabled = 'true' AND is_mirror_serving_country (m, v_country_code);
END;
$$
LANGUAGE plpgsql;


-- Determine if a mirror serves content to a region
DROP FUNCTION IF EXISTS is_mirror_serving_region;
CREATE OR REPLACE FUNCTION is_mirror_serving_region (v_mirror mirror, v_region_code varchar)
RETURNS BOOLEAN
AS
$$
DECLARE
    --  array of country codes that belong to this region.
    v_region_countries varchar[];
    -- loop variable for iterating the region country codes
    v_country_code varchar;
BEGIN
    -- initialize the countries belonging in the region.
    SELECT array_agg(code)
    INTO v_region_countries
    FROM country
    WHERE country.region_code = v_region_code;

    -- Exclude mirrors serving a single country if mirror country not in region
    IF v_mirror.country_only AND v_mirror.country_code != ALL(v_region_countries) THEN
        RETURN FALSE;
    END IF;

    -- Exclude mirrors serving a single region if not the same region.
    IF v_mirror.region_only AND v_mirror.region_code != v_region_code THEN
        RETURN FALSE;
    END IF;

    -- Exclude mirror if it is not serving all the countries in the region.
    IF array_length(coalesce(v_mirror.other_countries, '{}'), 1) > 0 THEN
	FOR v_country_code IN SELECT unnest(v_region_countries)
	LOOP
	    IF v_country_code NOT IN (SELECT unnest(v_mirror.other_countries)) THEN
		RETURN FALSE;
	    END IF;
	END LOOP;
    END IF;

    RETURN TRUE;
END;
$$
LANGUAGE plpgsql;


-- Get enabled mirrors serving content to a region
DROP FUNCTION IF EXISTS get_enabled_mirrors_serving_region;
CREATE OR REPLACE FUNCTION get_enabled_mirrors_serving_region (v_region_code varchar)
RETURNS SETOF mirror
AS
$$
BEGIN
    RETURN QUERY
	SELECT * FROM mirror m
	WHERE enabled = 'true' AND is_mirror_serving_region (m, v_region_code);
END;
$$
LANGUAGE plpgsql;


-- Determine if a test result is possible with the current MB configuration
DROP FUNCTION IF EXISTS is_mb_possible;
CREATE OR REPLACE FUNCTION is_mb_possible (v_test test)
RETURNS BOOLEAN
AS
$$
DECLARE
    -- mirror the test was run against.
    v_mirror mirror%rowtype;
    -- country in which the test was run from
    v_country country%rowtype;
BEGIN
    -- initialize the mirror for the test.
    SELECT * FROM mirror
    INTO v_mirror
    WHERE v_test.mirror_url = mirror.base_url;

    -- initialize the country for the test
    v_country := get_country_by_code(v_test.country_code);

    -- Exclude tests for mirrors with country_only if test not in the same country
    IF v_mirror.country_only AND v_mirror.country_code != v_test.country_code THEN
	RETURN FALSE;
    END IF;

    -- Exclude tests for mirrors with region only if test not in the same region
    IF v_mirror.region_only AND v_mirror.region_code != v_country.region_code THEN
	RETURN FALSE;
    END IF;

    -- Exclude test if mirror serves multiple countries and test not in countries
    IF array_length(coalesce(v_mirror.other_countries, '{}'), 1) > 0
	AND v_test.country_code != ALL(v_mirror.other_countries)
    THEN
	RETURN FALSE;
    END IF;

    RETURN TRUE;
END;
$$
LANGUAGE plpgsql;


-- Calculate the percentage of each score in list of scores
DROP FUNCTION IF EXISTS scores_percentage;
CREATE OR REPLACE FUNCTION scores_percentage(scores float[])
RETURNS float[]
AS
$$
DECLARE
    total float := 0.0;
    result float[] := '{}';
BEGIN
    SELECT SUM(score) FROM unnest(scores) AS score
    INTO total;

    result := ARRAY(
	SELECT (score / total)
	FROM unnest(scores) AS score
    );

    RETURN result;
END;
$$
LANGUAGE plpgsql;


-- Calculate the median speed across speeds
DROP FUNCTION IF EXISTS median_speed;
CREATE OR REPLACE FUNCTION median_speed (speeds float[])
RETURNS float
AS
$$
DECLARE
    result float := 0.0;
BEGIN
    SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY speed)
    INTO result
    FROM unnest(speeds) AS speed;

    RETURN result;
END;
$$
LANGUAGE plpgsql;


-- Get percentage score of a mirror from mirrors
DROP FUNCTION IF EXISTS percentage_score_for_mirror;
CREATE OR REPLACE FUNCTION percentage_score_for_mirror(
    v_mirror_id varchar, v_mirror_ids varchar[]
)
RETURNS float
AS
$$
DECLARE
    -- position of the mirror in the mirrors array.
    v_mirror_index integer;
    -- respective scores of the mirrors according to position
    v_mirror_scores integer[] := '{}';
    -- respective percentage scores of the mirrors according to position
    v_mirror_percentage_scores float[];
    -- loop variables for iterating through the mirror_ids array
    current_mirror_id varchar;
    current_mirror mirror%rowtype;
BEGIN
    v_mirror_index := array_position(v_mirror_ids, v_mirror_id);

    IF v_mirror_index IS NULL THEN
	RETURN 0.0;
    END IF;

    FOR current_mirror_id IN SELECT unnest(v_mirror_ids)
    LOOP
	current_mirror := get_mirror_by_id(current_mirror_id);
	v_mirror_scores := array_append(v_mirror_scores, current_mirror.score);
    END LOOP;


    v_mirror_percentage_scores := scores_percentage(v_mirror_scores);
    RETURN v_mirror_percentage_scores[v_mirror_index];
END;
$$
LANGUAGE plpgsql;


-- Compute performance for country/mirror cell
DROP FUNCTION IF EXISTS compute_country_performance;
CREATE OR REPLACE FUNCTION compute_country_performance (
    v_mirror_id varchar,
    v_country_code varchar,
    start_date date,
    end_date date
)
RETURNS float
AS
$$
DECLARE
    -- country with the specified country code
    v_current_country country%rowtype;
    -- speed of tests in the country
    v_test_speeds float[];
    v_tests_median_speed float;
    -- array of mirrors that also serve content for this country/region
    v_mirror_ids varchar[];
    -- weight of the mirror relative to similar mirrors serving conent
    v_mirror_weight float := 0.0;
BEGIN
    v_current_country := get_country_by_code(v_country_code);

    -- get all the speeds for the tests matching the MB configuration in the country.
    WITH all_tests AS (
	SELECT * FROM get_all_tests_for_country (
	    v_mirror_id, v_country_code, start_date, end_date
	) AS t
	WHERE is_mb_possible(t)
    )
    SELECT array_agg(speed) INTO v_test_speeds
    FROM all_tests;

    v_tests_median_speed := median_speed(v_test_speeds);

    -- compute the ids of the mirrors in the same country.
    SELECT array_agg(id) INTO v_mirror_ids
    FROM get_enabled_mirrors_in_country(v_country_code);

    IF coalesce(array_length(v_mirror_ids, 1), 0) > 0 THEN
	v_mirror_weight := percentage_score_for_mirror(v_mirror_id, v_mirror_ids);
	RETURN v_mirror_weight * v_tests_median_speed;
    END IF;

    -- no mirror for this country, check if there are mirrors in the region.
    SELECT array_agg(id) INTO v_mirror_ids
    FROM get_enabled_mirrors_in_region(v_current_country.region_code);

    IF coalesce(array_length(v_mirror_ids, 1), 0) > 0 THEN
	v_mirror_weight := percentage_score_for_mirror(v_mirror_id, v_mirror_ids);
	RETURN v_mirror_weight * v_tests_median_speed;
    END IF;

    -- no mirror in region, default to fallback mirrors
    SELECT array_agg(id) INTO v_mirror_ids
    FROM get_enabled_mirrors_serving_country(v_country_code);

    v_mirror_weight := percentage_score_for_mirror(v_mirror_id, v_mirror_ids);
    RETURN v_mirror_weight * v_tests_median_speed;
END;
$$
LANGUAGE plpgsql;


-- compute performance for region/mirror cell
DROP FUNCTION IF EXISTS compute_region_performance;
CREATE OR REPLACE FUNCTION compute_region_performance(
    v_mirror_id varchar,
    v_region_code varchar,
    start_date date,
    end_date date
)
RETURNS float
AS
$$
DECLARE
    -- region with the specified region code
    v_current_region region%rowtype;
    -- speeds of tests in the region
    v_test_speeds float[];
    v_tests_median_speed float;
    -- array of mirrors that also serve content in this region.
    v_mirror_ids varchar[];
    v_mirror_weight float := 0.0;
BEGIN
    v_current_region := get_region_by_code(v_region_code);

    -- get all the scores for the tests matching the MB configuration in the region
    WITH all_tests AS (
	SELECT * FROM get_all_tests_for_region (
	    v_mirror_id, v_current_region.code, start_date, end_date
	) AS t
	WHERE is_mb_possible(t)
    )
    SELECT array_agg(speed) INTO v_test_speeds
    FROM all_tests;

    v_tests_median_speed := median_speed(v_test_speeds);

    -- check if there are mirrors in the region.
    SELECT array_agg(id) INTO v_mirror_ids
    FROM get_enabled_mirrors_in_region(v_current_region.code);

    IF coalesce(array_length(v_mirror_ids, 1), 0) > 0 THEN
	v_mirror_weight := percentage_score_for_mirror(v_mirror_id, v_mirror_ids);
	RETURN v_mirror_weight * v_tests_median_speed;
    END IF;

    -- no mirror in region, default to fallback mirrors for the region.
    SELECT array_agg(id) INTO v_mirror_ids
    FROM get_enabled_mirrors_serving_region(v_current_region.code);

    v_mirror_weight := percentage_score_for_mirror(v_mirror_id, v_mirror_ids);
    RETURN v_mirror_weight * v_tests_median_speed;
END;
$$
LANGUAGE plpgsql;
