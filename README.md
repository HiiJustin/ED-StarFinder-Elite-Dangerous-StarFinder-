# Starfinder_V1.17

Starfinder_V1.17 is a Python tool designed for Elite Dangerous players. It allows you to search for a star system by name and retrieves all surrounding star systems within a user-defined range by leveraging the EDSM API. The tool features caching, operation & error logging, 3D plotting using Plotly, and a modern Tkinter GUI.

## Features

- Retrieve system coordinates from the EDSM system API.
- Query nearby star systems using the sphere-systems API.
- Cache API responses (valid for 86400 seconds) to reduce redundant requests.
- Operation and error logging.
- 3D visualization of star systems with customizable dimensions and star color mappings.
- Tkinter-based GUI with a “More Details” toggle, animated loading indicator, dark mode, and more.
- Import/Export functionality for search results.

## Installation

### Prerequisites

Ensure you have the following installed on your machine:

- **Python 3**  
  You can download Python from the [official website](https://www.python.org/downloads/). Follow the installation instructions for your operating system.

- **Git**  
  Download and install Git from the [official website](https://git-scm.com/downloads).

### Cloning the Repository

1. Open your terminal (or Command Prompt on Windows) and run:

   ```bash
   git clone https://github.com/yourusername/Starfinder_V1.17.git
