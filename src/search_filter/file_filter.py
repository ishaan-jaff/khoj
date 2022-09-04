# Standard Packages
import re
import fnmatch

# External Packages
import torch

# Internal Packages
from src.search_filter.base_filter import BaseFilter


class FileFilter(BaseFilter):
    file_filter_regex = r'file:"(.+?)" ?'

    def __init__(self, entry_key='file'):
        self.entry_key = entry_key

    def load(self, *args, **kwargs):
        pass

    def can_filter(self, raw_query):
        return re.search(self.file_filter_regex, raw_query) is not None

    def apply(self, raw_query, raw_entries, raw_embeddings):
        # Extract file filters from raw query
        raw_files_to_search = re.findall(self.file_filter_regex, raw_query)
        if not raw_files_to_search:
            return raw_query, raw_entries, raw_embeddings

        # Convert simple file filters with no path separator into regex
        # e.g. "file:notes.org" -> "file:.*notes.org"
        files_to_search = []
        for file in sorted(raw_files_to_search):
            if '/' not in file and '\\' not in file and '*' not in file:
                files_to_search += [f'*{file}']
            else:
                files_to_search += [file]
        query = re.sub(self.file_filter_regex, '', raw_query).strip()
        included_entry_indices = [id for id, entry in enumerate(raw_entries) for search_file in files_to_search if fnmatch.fnmatch(entry[self.entry_key], search_file)]
        if not included_entry_indices:
            return query, [], torch.empty(0)

        entries = [entry for id, entry in enumerate(raw_entries) if id in included_entry_indices]
        embeddings = torch.index_select(raw_embeddings, 0, torch.tensor(list(included_entry_indices)))

        return query, entries, embeddings
