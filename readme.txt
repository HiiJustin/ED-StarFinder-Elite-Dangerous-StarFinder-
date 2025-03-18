Starfinder_V1.17 - Elite Dangerous Star Finder
===============================================
Version: 1.17b1
Created by The Omega Colonization Project
Contributors: HiiJustin, HadominusX

Overview:
---------
Starfinder_V1.17 is a Python tool for Elite Dangerous players. It allows you to search for a star system by name and retrieves all surrounding star systems within a user-defined range by leveraging the EDSM API. The tool caches data (valid for 86400 seconds), logs operations and errors, and provides a modernized Tkinter GUI with extra features like:
 • A “More Details” toggle to show/hide additional system information.
 • A scrollable dropdown for selecting the search radius (values 4 to 40 ly).
 • A custom animated loading indicator.
 • 3D plotting using Plotly with configurable dimensions and star color mappings.
 • Import/Export functionality for search results.

Features:
---------
• Retrieves system coordinates from the EDSM system API.
• Queries nearby star systems using the sphere-systems API.
• Caching of API responses to reduce redundant requests.
• Detailed operation and error logging.
• 3D visualization of the star systems.
• A Tkinter-based GUI with Dark Mode and other usability enhancements.

Installation:
-------------
1. Ensure you have Python 3 installed.
2. Install the required Python packages by running:
   pip install -r requirements.txt

Usage:
------
1. Run the script:
   python3 Starfinder_V1.17.py
2. Enter the name of the star you wish to search.
3. Choose the desired search radius from the dropdown.
4. Click "Search" to retrieve and display the nearby star systems.
5. Use the menu options to export/import results, clear cache, or configure 3D plot settings.

Directory Structure:
--------------------
Upon running, the application creates an "EDStarFinderData" directory with subdirectories for:
 • cache  - for storing API response data.
 • logs   - for operation and error logs.
 • results- for exported search results.

API Endpoints Used:
-------------------
1. System Details:
   https://www.edsm.net/api-v1/system?systemName={systemName}&showCoordinates=1
2. Sphere Systems (by coordinates):
   https://www.edsm.net/api-v1/sphere-systems?x={x}&y={y}&z={z}&radius={radius}&showCoordinates=1&showId=1&showDistance=1&showPrimaryStar=1

Support:
--------
For issues, suggestions, or contributions, please contact the developers or check the project repository.

License:
--------
[Specify your license here, if applicable]

Enjoy exploring the galaxy in Elite Dangerous!
