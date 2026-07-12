-- Public read access for FastAPI (service_role key) and PostgREST
GRANT SELECT, INSERT, UPDATE ON TABLE public.gyms TO authenticated, service_role;
GRANT SELECT, INSERT, UPDATE ON TABLE public.crowd_readings TO authenticated, service_role;
GRANT SELECT, INSERT, UPDATE ON TABLE public.crowd_predictions TO authenticated, service_role;
GRANT SELECT, INSERT, UPDATE ON TABLE public.weather_forecasts TO authenticated, service_role;