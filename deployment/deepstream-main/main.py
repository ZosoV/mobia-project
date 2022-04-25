import argparse

from pipeline import Pipeline

if __name__ == '__main__':
    description = 'Deepstream Main Application set a config file'
    parser = argparse.ArgumentParser(description)
    
    parser.add_argument('--config',
                        default = 'configs/global_config.cfg',
                        type    = str,
                        help    = 'global configuration file')

    args = parser.parse_args()
    new_pipeline = Pipeline(path_config_global = args.config )
    new_pipeline.run_main_loop()