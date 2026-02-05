# Media Compressor

A powerful, universal batch media compressor for **Video** and **Images**.  
Optimizes your media library to save space while maintaining high visual quality.

## Features

### 🎥 Video Compression
- **High Efficiency**: Uses **H.265 (HEVC)** for maximum compression.
- **Hardware Acceleration**: Automatic **NVIDIA GPU (NVENC)** detection and usage.
- **Hybrid Processing**: Supports simultaneous CPU and GPU workers for maximum throughput.
- **Smart Quality**: Configurable CRF (Constant Rate Factor) and Presets.
- **Auto-Config**: Automatically detects CPU threads and VRAM to set optimal worker counts.

### 🖼️ Image Compression
- **Modern Formats**: Compresses images to **WebP** by default (Superior compression vs JPEG/PNG).
- **Format Support**: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.webp`.
- **Visually Lossless**: Defaults to High Quality (90) to ensure images look great.
- **Flexible**: Option to keep original format (e.g., optimize JPEG without converting to WebP).

## Installation

This project is managed with `uv`.

1. **Prerequisites**
   - **FFmpeg**: Must be installed and accessible in your system PATH.
   - **Python**: 3.12+

2. **Install Dependencies**
   ```bash
   uv sync
   ```

## Usage

Run the script using `uv run`.

### Basic Usage
Compress all videos and images in a folder:
```bash
uv run main.py /path/to/media_folder
```

### Automatic Configuration (Recommended)
Automatically detect hardware and maximize workers:
```bash
uv run main.py --auto-config /path/to/media_folder
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--output-path`, `-o` | Output directory or file path. | Source location |
| `--delete-source` | **DELETE** original file after successful compression. | False |
| `--auto-config` | Automatically set CPU/GPU worker counts. | False |
| `--cpu-workers` | Number of CPU workers. | 0 |
| `--gpu-workers` | Number of GPU workers. | 0 |

#### Video Options
| Flag | Description | Default |
|------|-------------|---------|
| `--crf` | CRF value (Lower = Better Quality). | 23 |
| `--preset` | Compression preset (e.g., medium, slow). | medium |

#### Image Options
| Flag | Description | Default |
|------|-------------|---------|
| `--image-quality` | Image quality (1-100). | 90 |
| `--keep-format` | Keep original extension instead of WebP. | False |

#### General Options
| Flag | Description | Default |
|------|-------------|---------|
| `--no-scan-duration` | Skip scanning total video duration (Use file count progress). | False |

### Examples

**Compress videos with high quality (CRF 20):**
```bash
uv run main.py /movies --crf 20
```

**Compress images but keep them as JPEGs (don't convert to WebP):**
```bash
uv run main.py /photos --keep-format
```

**Full automation (Auto-config + Delete source):**
```bash
uv run main.py --auto-config --delete-source /downloads
```

## Contributing
- **Format**: Python (managed by `uv`).
- **Style**: Uses `rich` for terminal UI.
