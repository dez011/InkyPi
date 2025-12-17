# app_registry.py

import os
import importlib
import logging
from utils.app_utils import resolve_path
# from utils import app_utils
from pathlib import Path

logger = logging.getLogger(__name__)
PLUGINS_DIR = 'plugins'
PLUGIN_CLASSES = {}

def load_plugins(plugins_config):
    plugins_module_path = Path(resolve_path(PLUGINS_DIR))
    logging.info("Plugins root: %s", plugins_module_path)
    try:
        found_folders = sorted([p.name for p in plugins_module_path.iterdir() if p.is_dir()])
    except Exception as e:
        found_folders = []
        logging.error("Failed to enumerate plugin folders under %s: %s", plugins_module_path, e)
    logging.info("Plugin folders found:\n%s", "\n".join(found_folders) if found_folders else "(none)")

    # Show incoming plugin configs (one per line)
    try:
        cfg_lines = []
        for pc in plugins_config:
            pid = pc.get("id")
            pclazz = pc.get("class")
            pmod = pc.get("module")
            cfg_lines.append(f"- id={pid}  class={pclazz}  module={pmod}")
        logging.info("Plugins config entries:\n%s", "\n".join(cfg_lines))
    except Exception as e:
        logging.error("Failed to print plugins_config summary: %s", e)

    for plugin in plugins_config:
        plugin_id = plugin.get('id')
        if plugin.get("disabled", False):
            logging.info(f"Plugin {plugin_id} is disabled, skipping.")
            continue

        plugin_dir = plugins_module_path / plugin_id
        logging.info("Checking plugin id '%s' in folder %s", plugin_id, plugin_dir)
        if not plugin_dir.is_dir():
            logging.error("Could not find plugin directory %s for '%s', skipping.", plugin_dir, plugin_id)
            logging.info("Existing plugin folders are:\n%s", "\n".join(found_folders) if found_folders else "(none)")
            continue

        logging.info("Expecting module file: %s", plugin_dir / f"{plugin_id}.py")
        module_path = plugin_dir / f"{plugin_id}.py"
        if not module_path.is_file():
            try:
                available = sorted([p.name for p in plugin_dir.iterdir() if p.suffix == ".py"])
            except Exception:
                available = []
            logging.error("Could not find module file %s for '%s'. Available .py files: %s. Skipping.",
                          module_path, plugin_id, ", ".join(available) or "(none)")
            continue

        module_name = f"plugins.{plugin_id}.{plugin_id}"
        try:
            module = importlib.import_module(module_name)
            plugin_class = getattr(module, plugin.get("class"), None)

            if plugin_class:
                PLUGIN_CLASSES[plugin_id] = plugin_class(plugin)
                logging.info("Registered plugin '%s' -> %s.%s", plugin_id, module_name, plugin.get("class"))
            else:
                logging.error("Class '%s' not found in %s for plugin id '%s'", plugin.get("class"), module_name, plugin_id)

        except ImportError as e:
            logging.error(f"Failed to import plugin module {module_name}: {e}")

    logging.info("Final registered plugins:\n%s", "\n".join(f"{pid}: {cls}" for pid, cls in PLUGIN_CLASSES.items()) or "(none)")

def get_plugin_instance(plugin_config):
    plugin_id = plugin_config.get("id")
    logging.info(plugin_config)
    logging.info("Registered plugins:\n" + "\n".join(f"{pid}: {cls}" for pid, cls in PLUGIN_CLASSES.items()))    # Retrieve the plugin class factory function
    plugin_class = PLUGIN_CLASSES.get(plugin_id)
    
    if plugin_class:
        # Initialize the plugin with its configuration
        return plugin_class
    else:
        raise ValueError(f"Plugin '{plugin_id}' is not registered.")