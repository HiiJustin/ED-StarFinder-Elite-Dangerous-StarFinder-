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
   ```

2. Change into the project directory:

   ```bash
   cd Starfinder_V1.17
   ```

### Setting Up the Python Environment

It is recommended to use a virtual environment to manage dependencies.

1. Create a virtual environment (optional but recommended):

   ```bash
   python3 -m venv venv
   ```

2. Activate the virtual environment:

   - **On macOS/Linux:**

     ```bash
     source venv/bin/activate
     ```

   - **On Windows:**

     ```bash
     venv\Scripts\activate
     ```

3. Install the required Python packages using `requirements.txt`:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Ensure that any required images (`ship.png` and `planet.png`) are in the same directory as the script.

2. Run the application with:

   ```bash
   python3 Starfinder_V1.17.py
   ```

3. Enter the star name and choose your search radius from the dropdown in the GUI, then click **Search**.

4. Use the menu options to export/import results, clear cache, or configure 3D plot settings.

## Directory Structure

Upon running the application, the following directories are automatically created:

- **EDStarFinderData**
  - **cache**  - Stores API response data.
  - **logs**   - Contains operation and error logs.
  - **results**- For exported search results.

## Contributing

Contributions are welcome! If you would like to contribute to this project:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature-name`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature-name`).
5. Open a Pull Request.

## License

[Specify your license here if applicable.]

## Support

If you encounter any issues or have suggestions, please open an issue in the GitHub repository or contact the project maintainers.

---

Enjoy exploring the galaxy in Elite Dangerous!
```

--- 

This README provides clear instructions on installing Python and Git, setting up the environment, and running the project using the provided requirements.txt.
