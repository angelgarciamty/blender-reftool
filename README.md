# RefTool Blender Edition (v5.3)

RefTool is a professional add-on designed to optimize the sculpting and modeling workflow in Blender. It allows you to manage multiple reference images through a dedicated camera system with persistent orbit controls.

This tool was created taking inspiration from **RefTool 3.0 for Maya by Kanstantsin Vershalovich**, adapting and expanding its features for the Blender ecosystem.

## Main Features

- **Reference Management:** Load images directly as reference cameras (`REF_`). The add-on automatically isolates the active camera, hiding the rest to keep the viewport clean.
- **3D Orbit Controls:** Adjust horizontal rotation, vertical rotation, and camera roll without losing focus on the center of the scene.
- **Lens Simulation:** Integrated focal length control to adjust the perspective of the reference (perfect for matching lens distortions in real photos).
- **On-Screen 2D Adjustments:** Full control over opacity (Alpha), scale, rotation, and offset (X/Y) of the background image directly from the panel.
- **Movement History (Custom Undo):** Includes an internal memory system that records up to 10 orbital adjustment steps, allowing you to undo specific view changes without affecting your mesh's edit history.
- **Quick Navigation:** Quick access buttons for orthographic views (Top, Front, Side) and perspective.

## Installation

1. Download the `.py` file from this repository.
2. In Blender, go to **Edit > Preferences > Add-ons**.
3. Click on **Install...** and select the downloaded file.
4. Check the box for **Interface: RefTool Blender Edition**.

## Usage

Once installed, you will find the panel in the **Sidebar (N key)** of the 3D Viewport, under the **RefTool** tab.

1. Click on **Load New Reference** to import an image.
2. Use the **Orbit H**, **Orbit V**, and **Zoom** sliders to position your reference in 3D space.
3. If you make a mistake while adjusting, use the **Undo** button from the internal history.
4. Switch between different references by simply clicking their names in the "My References" list.

## Technical Specifications

- **Version:** 5.3
- **Compatibility:** Blender 3.0.0 or higher.
- **Author:** Angel Iván García Santamaría

---
*Inspired by the original work of Kanstantsin Vershalovich for Autodesk Maya.*