class SvgPathHierarchy():
    def __init__(self, root_path=None, child_paths=None):
        if child_paths is None:
            child_paths = list()
        self._root_path = root_path
        self._child_paths = child_paths

    def root_path(self):
        assert self._root_path
        return self._root_path

    def child_paths(self):
        return self._child_paths

    def set_root_path(self, new_root_path):
        self._root_path = new_root_path

    def add_child_path(self, child_path):
        self._child_paths.append(child_path)
