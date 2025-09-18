from mmu import MMU
import random

class RandMMU(MMU):
    def __init__(self, frames):
        # TODO: Constructor logic for RandMMU
        self.num_frames = int(frames)
        self.frames = [None] * self.num_frames
        self.page_to_frame = {}
        self._disk_reads = 0
        self._disk_writes = 0
        self._page_faults = 0
        self._debug = False
        self._free = list(range(self.num_frames))
        pass

    def set_debug(self):
        # TODO: Implement the method to set debug mode
        self._debug = True
        pass

    def reset_debug(self):
        # TODO: Implement the method to reset debug mode
        self._debug = False
        pass

    def read_memory(self, page_number):
        # TODO: Implement the method to read memory
        self._access(page_number, False)
        pass

    def write_memory(self, page_number):
        # TODO: Implement the method to write memory
        self._access(page_number, True)
        pass

    def get_total_disk_reads(self):
        # TODO: Implement the method to get total disk reads
        return self._disk_reads

    def get_total_disk_writes(self):
        # TODO: Implement the method to get total disk writes
        return self._disk_writes

    def get_total_page_faults(self):
        # TODO: Implement the method to get total page faults
        return self._page_faults 
    
    def _access(self, page, is_write):
        idx = self.page_to_frame.get(page)
        if idx is not None:
            entry = self.frames[idx]
            if entry is not None:
                if is_write:
                    entry["dirty"] = True
                else:
                    entry["dirty"] = entry.get("dirty", False)
            return
        
        self._page_faults += 1

        if self._free:
            idx = self._free.pop(0)
        else:
            idx = self._choose_victim()
            self._evict(idx)

        self._disk_reads += 1
        self.frames[idx] = {"page": page, "dirty": bool(is_write)}
        self.page_to_frame[page] = idx
        if is_write and self.frames[idx] is not None:
            self.frames[idx]["dirty"] = True

    def _choose_victim(self):
        if self.num_frames <= 1:
            return 0
        idx = random.randrange(0, self.num_frames)
        while self.frames[idx] is None:
            idx = random.randrange(0, self.num_frames)
        return idx
    
    def _evict(self, idx):
        entry = self.frames[idx]
        if entry is None:
            return
        if entry.get("dirty"):
            self._disk_writes += 1
        old_page = entry.get("page")
        if old_page in self.page_to_frame:
            del self.page_to_frame[old_page]
        self.frames[idx] = None
