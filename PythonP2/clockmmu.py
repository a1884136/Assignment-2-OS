from mmu import MMU


class ClockMMU(MMU):

    def __init__(self, frames: int):
        self.frames_capacity = int(frames)

        self._page_faults = 0
        self._disk_reads = 0
        self._disk_writes = 0

        self.frame_page = [None] * self.frames_capacity   
        self.dirty      = [False] * self.frames_capacity  
        self.ref        = [0] * self.frames_capacity      
        self.page_to_frame = {}                           

        self.hand = 0

        self.debug = False

    def set_debug(self):
        self.debug = True

    def reset_debug(self):
        self.debug = False

    def read_memory(self, page_number: int):
        self._access(page_number, is_write=False)

    def write_memory(self, page_number: int):
        self._access(page_number, is_write=True)

    def get_total_disk_reads(self) -> int:
        return self._disk_reads

    def get_total_disk_writes(self) -> int:
        return self._disk_writes

    def get_total_page_faults(self) -> int:
        return self._page_faults

    def _access(self, page: int, is_write: bool):
        frame = self.page_to_frame.get(page)

        if frame is not None:
            if is_write:
                self.dirty[frame] = True
            self.ref[frame] = 1
            if self.debug:
                print(f"{'writting' if is_write else 'reading'}   {page:8d}")
            return

        self._page_faults += 1
        self._disk_reads  += 1
        if self.debug:
            print(f"Page fault {page:8d}")

        free_idx = self._find_free_frame()
        if free_idx is not None:
            self._install(free_idx, page, is_write)
            if self.debug:
                print(f"{'writting' if is_write else 'reading'}   {page:8d}")
            return

        victim_idx = self._evict_clock()
        self._install(victim_idx, page, is_write)
        if self.debug:
            print(f"{'writting' if is_write else 'reading'}   {page:8d}")

    def _find_free_frame(self):
        for i in range(self.frames_capacity):
            if self.frame_page[i] is None:
                return i
        return None

    def _install(self, frame_idx: int, page: int, is_write: bool):
        self.frame_page[frame_idx] = page
        self.page_to_frame[page] = frame_idx
        self.dirty[frame_idx] = bool(is_write)
        self.ref[frame_idx] = 1

    def _advance_hand(self):
        self.hand = (self.hand + 1) % self.frames_capacity

    def _evict_clock(self) -> int:
        while True:
            if self.frame_page[self.hand] is not None:
                if self.ref[self.hand] == 0:
                    victim_frame = self.hand
                    victim_page = self.frame_page[victim_frame]

                    if self.dirty[victim_frame]:
                        self._disk_writes += 1
                        if self.debug:
                            print(f"Disk write {victim_page:8d}")
                    else:
                        if self.debug:
                            print(f"Discard    {victim_page:8d}")

                    del self.page_to_frame[victim_page]
                    self.frame_page[victim_frame] = None
                    self.dirty[victim_frame] = False

                    self._advance_hand()
                    return victim_frame
                else:
                    self.ref[self.hand] = 0

            self._advance_hand()
