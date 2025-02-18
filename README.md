<!------------------------------------------------------------------->

# 3DARRE (working project name)

**Authors:**

William (Zhiwen) Chen (willc@illinois.edu), *project manager*

Evan M. Matthews (evanmm3@illinois.edu), *lead programmer*

**3D** **A**coustic **R**oom **R**endering **E**nvironment (3DARRE) is a graphical application for rendering and analyzing acoustical properties of 3D spaces via meshes. The projects internals function on [pyroomacoustics](https://github.com/LCAV/pyroomacoustics), a library for testing and simulating acoustics algorithms written by Robin Scheibler. 

<!------------------------------------------------------------------->

## Setup

1. Clone the repository

    ```
    $ git clone https://github.com/ematth/3DARRE.git
    ```

2. Setup your virtual environment (venv) and install necessary packages

    ```
    $ python3 -m venv venv
    $ source venv/bin/activate
    (venv) $ pip install -r requirements.txt
    ```
3. Open the existing rendering GUI:

    ```
    $ cd Software_3D_engine
    $ python3 main.py
    ```

If everything is setup correctly, you will see a spinning rendering of a potted plant 🪴

<!------------------------------------------------------------------->

## Controls

- **AWSD** control camera movement on the XY-plane.

- **Left and Right Arrows** control camera rotation on the XY-plane.

- **Up and Down Arrows** control camera rotation on the YZ-plane.

(*This makes more sense when you start playing around in the renderer.*)


<!------------------------------------------------------------------->


## Credits/Licenses

[Pyroomacoustics](https://github.com/LCAV/pyroomacoustics): 2014-2017 EPFL-LCAV, MIT License 2014-2017 


[Software_3D_engine](https://github.com/StanislavPetrovV/Software_3D_engine): StanislavPetrovV, MIT License 2020


<!------------------------------------------------------------------->