from mmu import MMU

class LruMMU(MMU):
    def __init__(self, frames):
        """Initialize LRU Memory Management Unit with all necessary data structures"""
        # Basic memory configuration
        self.frames = frames
        
        # Core data structures for page management
        self.page_table = {}  # Maps page_number -> frame_index (where is page X?)
        self.frame_table = [None] * frames  # Maps frame_index -> page_number (what's in frame Y?)
        self.dirty_bits = [False] * frames  # Is frame Y dirty (modified since loaded)?
        self.access_time = [0] * frames  # When was frame Y last accessed? (key for LRU)
        self.free_frames = list(range(frames))  # Which frames are currently empty?
        
        # Global time counter - incremented on every memory access
        self.current_time = 0
        
        # Statistics tracking (required by assignment)
        self.disk_reads = 0
        self.disk_writes = 0
        self.page_faults = 0
        
        # Debug mode for detailed output
        self.debug = False

    def set_debug(self):
        """Enable debug messages - shows detailed step-by-step operations"""
        self.debug = True

    def reset_debug(self):
        """Disable debug messages - run quietly"""
        self.debug = False

    def read_memory(self, page_number):
        """
        Handle a read operation from memory
        Could result in page hit (already in memory) or page fault (need to load)
        """
        self.current_time += 1  # Every access advances our time counter
        
        if page_number in self.page_table:
            # Page hit - the page is already loaded in memory
            frame_index = self.page_table[page_number]  # Find which frame has it
            self.access_time[frame_index] = self.current_time  # Update LRU tracking
            
            if self.debug:
                print(f"Page hit: reading page {page_number} from frame {frame_index}")
        else:
            # Page fault - page is not in memory, need to load it
            self._handle_page_fault(page_number, is_write=False)

    def write_memory(self, page_number):
        """
        Handle a write operation to memory
        If page hit, mark as dirty. If page fault, load then mark dirty.
        """
        self.current_time += 1  # Every access advances our time counter
        
        if page_number in self.page_table:
            # Page hit - page is already in memory
            frame_index = self.page_table[page_number]
            self.dirty_bits[frame_index] = True  # Mark as dirty (modified)
            self.access_time[frame_index] = self.current_time  # Update LRU tracking
            
            if self.debug:
                print(f"Page hit: writing to page {page_number} in frame {frame_index} (now dirty)")
        else:
            # Page fault - need to load page first, then it will be dirty
            self._handle_page_fault(page_number, is_write=True)

    def get_total_disk_reads(self):
        """Return total disk reads performed (equals page faults)"""
        return self.disk_reads

    def get_total_disk_writes(self):
        """Return total disk writes performed (dirty page evictions)"""
        return self.disk_writes

    def get_total_page_faults(self):
        """Return total page faults that have occurred"""
        return self.page_faults
    
    def _handle_page_fault(self, page_number, is_write=False):
        """
        Handle a page fault by loading the page into memory
        
        WHY THIS HELPER METHOD EXISTS:
        Both read_memory() and write_memory() need to handle page faults in exactly
        the same way. Without this helper, we would have to copy-paste identical
        page fault handling code in both methods, violating the DRY principle
        (Don't Repeat Yourself).
        
        BENEFITS OF THIS APPROACH:
        1. Code Reuse: One implementation shared by both read and write operations
        2. Maintainability: Bug fixes or improvements only need to be made once
        3. Consistency: Guarantees read and write faults behave identically
        4. Readability: read_memory() and write_memory() focus on their unique logic
        """
        # Record this page fault and the disk read it requires
        self.page_faults += 1
        self.disk_reads += 1  # Loading from disk always requires a read
        self.current_time += 1  # This access gets a timestamp
        
        if self.debug:
            print(f"Page fault: need to load page {page_number}")
        
        # Find a frame to use for this page
        if self.free_frames:
            # Easy case - we have empty frames available
            frame_index = self.free_frames.pop(0)  # Take first free frame
            if self.debug:
                print(f"Using free frame {frame_index}")
        else:
            # Hard case - memory is full, must evict LRU page
            frame_index = self._find_lru_victim()
            old_page = self.frame_table[frame_index]  # What page are we evicting?
            
            if self.debug:
                print(f"Memory full - evicting LRU page {old_page} from frame {frame_index}")
            
            # If evicted page is dirty, write it back to disk
            if self.dirty_bits[frame_index]:
                self.disk_writes += 1
                if self.debug:
                    print(f"Evicted page {old_page} was dirty - writing to disk")
            
            # Remove old page from our tracking
            del self.page_table[old_page]  # Old page no longer in memory
        
        # Install new page in the selected frame
        self.frame_table[frame_index] = page_number  # Frame now contains new page
        self.page_table[page_number] = frame_index   # New page is in this frame
        self.dirty_bits[frame_index] = is_write      # Dirty if this is a write
        self.access_time[frame_index] = self.current_time  # Record when accessed
        
        if self.debug:
            print(f"Loaded page {page_number} into frame {frame_index}")
    
    def _find_lru_victim(self):
        """
        Find the Least Recently Used frame to replace
        
        WHY THIS HELPER METHOD EXISTS:
        The LRU replacement algorithm requires finding the frame with the oldest
        access time. This operation deserves its own method for several reasons:
        
        BENEFITS OF SEPARATION:
        1. Single Responsibility: This method has one job - find the LRU frame
        2. Testability: We can unit test the LRU logic independently
        3. Algorithm Clarity: The LRU selection logic is clearly separated from
           the page loading/eviction mechanics
        4. Future Flexibility: Easy to optimize (e.g., use heap) without changing
           the page fault handling code
        5. Debugging: Can add specific debug output for LRU decisions here
        
        ALTERNATIVE APPROACHES CONSIDERED:
        - Could inline this logic in _handle_page_fault(), but that would mix
          the "find victim" concern with the "handle fault" concern
        - Could use a more complex data structure like a heap, but simple linear
          search is fine for typical frame counts (usually < 100)
          
        Returns:
            int: Frame index containing the least recently used page
        """
        oldest_time = float('inf')  # Start with impossibly large time
        lru_frame_index = 0
        
        # Check every frame to find the one accessed longest ago
        for frame_index in range(self.frames):
            # Only consider frames that actually contain pages
            if self.frame_table[frame_index] is not None:
                if self.access_time[frame_index] < oldest_time:
                    oldest_time = self.access_time[frame_index]
                    lru_frame_index = frame_index
        
        return lru_frame_index
