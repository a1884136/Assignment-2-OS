from mmu import MMU


class ClockMMU(MMU):
    """
    A CLOCK page-replacement MMU.

    The CLOCK algorithm approximates LRU by keeping a "reference" (use) bit per frame.
    - On each access, the frame's reference bit is set to 1.
    - When a page fault occurs and no free frame exists, the "hand" sweeps:
        * If ref[hand] == 1: give a second chance (set it to 0) and advance.
        * If ref[hand] == 0: evict this frame.
    Dirty frames (written-to) incur a disk write on eviction.

    Public counters:
      - get_total_page_faults()
      - get_total_disk_reads()
      - get_total_disk_writes()
    """

    def __init__(self, frames: int):
        # Ensure we store a proper integer capacity for frames
        self.frames_capacity = int(frames)

        # Metrics for reporting
        self._page_faults = 0      # Count of page faults
        self._disk_reads = 0       # Count of reads (loads) from disk
        self._disk_writes = 0      # Count of writes (evictions of dirty pages)

        # Frame state arrays (indexed by frame index: 0..frames_capacity-1)
        self.frame_page = [None] * self.frames_capacity   # Which page is in each frame (None if free)
        self.dirty      = [False] * self.frames_capacity  # Dirty bit: True if page has been written since load
        self.ref        = [0] * self.frames_capacity      # Reference bit: set on access; cleared by clock sweep

        # Reverse lookup: page -> frame index (for O(1) hit checks)
        self.page_to_frame = {}

        # The "clock hand" pointer (index into frame arrays)
        self.hand = 0

        # Optional debug printing
        self.debug = False

    def set_debug(self):
        """Enable verbose debug printing."""
        self.debug = True

    def reset_debug(self):
        """Disable verbose debug printing."""
        self.debug = False

    def read_memory(self, page_number: int):
        """Read access to a page (sets its reference bit)."""
        self._access(page_number, is_write=False)

    def write_memory(self, page_number: int):
        """Write access to a page (sets reference bit and marks dirty)."""
        self._access(page_number, is_write=True)

    def get_total_disk_reads(self) -> int:
        """Return the total number of disk reads (page loads)."""
        return self._disk_reads

    def get_total_disk_writes(self) -> int:
        """Return the total number of disk writes (dirty evictions)."""
        return self._disk_writes

    def get_total_page_faults(self) -> int:
        """Return the total number of page faults encountered."""
        return self._page_faults

    def _access(self, page: int, is_write: bool):
        """
        Core access path:
        - If page is resident: set ref bit; mark dirty if write.
        - Else: page fault -> try a free frame, otherwise evict via CLOCK and install.
        """
        frame = self.page_to_frame.get(page)

        # Fast path: hit in memory
        if frame is not None:
            if is_write:
                self.dirty[frame] = True
            self.ref[frame] = 1  # mark as recently used
            if self.debug:
                print(f"{'writing' if is_write else 'reading'}   {page:8d}")
            return

        # Miss path: page fault → will need to read from disk
        self._page_faults += 1
        self._disk_reads  += 1
        if self.debug:
            print(f"Page fault {page:8d}")

        # Try to find a free frame first
        free_idx = self._find_free_frame()
        if free_idx is not None:
            self._install(free_idx, page, is_write)
            if self.debug:
                print(f"{'writing' if is_write else 'reading'}   {page:8d}")
            return

        # No free frame: evict a victim via CLOCK
        victim_idx = self._evict_clock()
        self._install(victim_idx, page, is_write)
        if self.debug:
            print(f"{'writing' if is_write else 'reading'}   {page:8d}")

    def _find_free_frame(self):
        """
        Return the index of a free frame if one exists, otherwise None.
        Free frames are represented by frame_page[i] is None.
        """
        for i in range(self.frames_capacity):
            if self.frame_page[i] is None:
                return i
        return None

    def _install(self, frame_idx: int, page: int, is_write: bool):
        """
        Install a page into the given frame:
        - Update frame_page and page_to_frame
        - Set dirty bit based on write access
        - Set reference bit (freshly used on install)
        """
        self.frame_page[frame_idx] = page
        self.page_to_frame[page] = frame_idx
        self.dirty[frame_idx] = bool(is_write)
        self.ref[frame_idx] = 1  # new page considered "referenced"

    def _advance_hand(self):
        """Advance the clock hand circularly to the next frame."""
        self.hand = (self.hand + 1) % self.frames_capacity

    def _evict_clock(self) -> int:
        """
        CLOCK eviction:
        Sweep frames with the hand until a frame with ref == 0 is found.
        - If ref == 1: clear it to 0 and continue (second chance).
        - If ref == 0: evict; write back if dirty; return that frame index.
        Hand advances after examining each frame; on eviction it also advances once more.
        """
        while True:
            # Only consider frames that are actually occupied
            if self.frame_page[self.hand] is not None:
                if self.ref[self.hand] == 0:
                    # Found victim: evict this frame
                    victim_frame = self.hand
                    victim_page = self.frame_page[victim_frame]

                    # If dirty, write back to disk
                    if self.dirty[victim_frame]:
                        self._disk_writes += 1
                        if self.debug:
                            print(f"Disk write {victim_page:8d}")
                    else:
                        if self.debug:
                            print(f"Discard    {victim_page:8d}")

                    # Remove mappings and clear frame state
                    del self.page_to_frame[victim_page]
                    self.frame_page[victim_frame] = None
                    self.dirty[victim_frame] = False
                    # Note: ref[victim_frame] will be set on install

                    # Advance hand once after eviction to avoid re-picking same slot immediately
                    self._advance_hand()
                    return victim_frame
                else:
                    # Give a second chance: clear ref and move on
                    self.ref[self.hand] = 0

            # Advance to check the next frame
            self._advance_hand()
