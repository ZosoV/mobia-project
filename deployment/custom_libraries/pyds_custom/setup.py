from distutils.core import setup
setup (name = 'pyds_custom',
       version = '1.0',
       description = """Install precompiled custom DeepStream Python bindings""",
       packages=[''],
       package_data={'': ['pyds_custom.so']},
       )
