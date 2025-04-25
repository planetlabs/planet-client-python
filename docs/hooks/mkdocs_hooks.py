from planet import __version__ as _pl_sdk_version

def on_config(config):
    """
    This is for injecting the package version into mkdocs
    config so it can be used in templates.
    """
    config["extra"]["planet_sdk_version"] = _pl_sdk_version
    return config
