# HTPBZ2
TMZ a Tar Parallel-BZip2 Compressor / Decompressor

This is a simple tool to compress and decompress files and dirs
The special things about this tool are:
- The compression is done through tar archiving tool and a parallelized BZip2 passage. Thus improving compression speed
- This app can handle Haiku specific attributes, saving them to the archive and restoring them to their relative files at decompression time.
- At your will you can save extra file and attribute checksums to check the integrity of decompressed files and attributes
- You can select the methods of compression and decompression: a single threaded process handled entirely by tar library to compress and decompress the archive OR a multi-threaded compression and a multi-threaded attributes extraction for boosted performances
- If you choose the boosted performances (which will require more system resources) you can also choose if work entirely on disk, or do partial process entirely in ram, thus saving disk writes and improving process speed
- You can select the compression level for your archive compression
- You can also select how many processors/cores use for your compression/decompression
- And you can select the block size to elaborate with tar and bz2