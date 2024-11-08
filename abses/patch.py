#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""PatchModule class
"""
from __future__ import annotations

import functools
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Literal,
    Optional,
    Tuple,
    Type,
    Union,
    cast,
)

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

from typing import TypeVar

import geopandas as gpd
import numpy as np
import pyproj
import rioxarray
import xarray as xr
from geocube.api.core import make_geocube
from loguru import logger
from mesa.space import Coordinate
from mesa_geo.raster_layers import RasterLayer
from numpy.typing import NDArray
from rasterio.enums import Resampling
from shapely import Geometry

from abses._bases.errors import ABSESpyError
from abses._bases.modules import Module, _ModuleFactory
from abses.cells import PatchCell
from abses.random import ListRandom
from abses.sequences import ActorsList
from abses.tools.func import get_buffer, set_null_values
from abses.viz.viz_nature import _VizNature

T = TypeVar("T", bound=PatchCell)

if TYPE_CHECKING:
    from abses.main import MainModel

CRS = "epsg:4326"
CellFilter: TypeAlias = Optional[str | np.ndarray | xr.DataArray | Geometry]
Raster: TypeAlias = Union[
    np.ndarray,
    xr.DataArray,
    xr.Dataset,
]


class _PatchModuleFactory(_ModuleFactory):
    def __init__(self, father) -> None:
        super().__init__(father)
        self.default_cls = PatchModule

    def __getitem__(self, name: str) -> PatchModule:
        return self.modules[name]

    def from_resolution(
        self,
        model: MainModel[Any, Any],
        name: Optional[str] = None,
        shape: Coordinate = (10, 10),
        crs: Optional[pyproj.CRS | str] = CRS,
        resolution: Union[int, float] = 1,
        module_cls: Optional[type[PatchModule]] = None,
        cell_cls: type[PatchCell] = PatchCell,
    ) -> PatchModule:
        """Create a layer from resolution.

        Parameters:
            model:
                ABSESpy Model that the new module belongs.
            name:
                Name of the new module.
                If None (by default), using lowercase of the '__class__.__name__'.
                E.g., class Module -> module.
            shape:
                Array shape (height, width) of the new module.
                For example, `shape=(3, 5)` means the new module stores 15 cells.
            crs:
                Coordinate Reference Systems.
                If passing a string object, should be able to parsed by `pyproj`.
                By default, we use CRS = "epsg:4326".
            resolution:
                Spatial Resolution when creating the coordinates.
                By default 1, it means shape (3, 5) will generate coordinates:
                {y: [0, 1, 2], x: [0, 1, 2, 3, 4]}.
                Similar, when using resolution=0.1,
                it will be {y: [.0, .1, .2], x: [.0, .1, .2, .3, .4]}.
            cell_cls:
                Class type of `PatchCell` to create.

        Returns:
            A new instance of self ("PatchModule").
        """
        to_create = cast(PatchModule, self._check_cls(module_cls=module_cls))
        height, width = shape
        total_bounds = [0, 0, width * resolution, height * resolution]
        return to_create(
            model,
            name=name,
            width=width,
            height=height,
            crs=crs,
            total_bounds=total_bounds,
            cell_cls=cell_cls,
        )

    def copy_layer(
        self,
        model: MainModel[Any, Any],
        layer: PatchModule,
        name: Optional[str] = None,
        module_cls: Optional[Type[PatchModule]] = None,
        cell_cls: Type[PatchCell] = PatchCell,
    ) -> PatchModule:
        """Copy an existing layer to create a new layer.

        Parameters:
            model:
                ABSESpy Model that the new module belongs.
            layer:
                Another layer to copy.
                These attributes will be copied:
                including the coordinates, the crs, and the shape.
            name:
                Name of the new module.
                If None (by default), using lowercase of the '__class__.__name__'.
                E.g., class Module -> module.
            cell_cls:
                Class type of `PatchCell` to create.

        Returns:
            A new instance of self ("PatchModule").
        """
        if not isinstance(layer, PatchModule):
            raise TypeError(f"{layer} is not a valid PatchModule.")
        to_create = cast(PatchModule, self._check_cls(module_cls=module_cls))
        return to_create(
            model=model,
            name=name,
            width=layer.width,
            height=layer.height,
            crs=layer.crs,
            total_bounds=layer.total_bounds,
            cell_cls=cell_cls,
        )

    def from_xarray(
        self,
        xda: xr.DataArray,
        model: MainModel[Any, Any],
        module_cls: Optional[Type[PatchModule]] = None,
        name: str | None = None,
        attr_name: str | None = None,
        apply_raster: bool = False,
        masked: bool = True,
        cell_cls: type[PatchCell] = PatchCell,
        **kwargs,
    ) -> PatchModule:
        """Create a new module instance from `xarray.DataArray` data."""
        # 如果 y 轴是从小到大的，反转它
        if xda.y[0].item() < xda.y[-1].item():
            xda.data = np.flipud(xda.data)
        # 创建模块
        to_create = cast(PatchModule, self._check_cls(module_cls=module_cls))
        module: PatchModule = to_create(
            model=model,
            name=name,
            width=xda.rio.width,
            height=xda.rio.height,
            crs=xda.rio.crs,
            total_bounds=xda.rio.bounds(),
            cell_cls=cell_cls,
        )
        if masked:
            module.mask = xda.notnull().to_numpy()
        if apply_raster:
            module.apply_raster(xda.to_numpy(), attr_name=attr_name, **kwargs)
        return module

    def from_vector(
        self,
        vector_file: str | Path | gpd.GeoDataFrame,
        resolution: Tuple[float, float] | float,
        model: MainModel[Any, Any],
        module_cls: Optional[Type[PatchModule]] = None,
        name: str | None = None,
        attr_name: Optional[str] = None,
        apply_raster: bool = False,
        masked: bool = True,
        cell_cls: type[PatchCell] = PatchCell,
    ) -> PatchModule:
        """Create a layer module from a shape file."""
        if isinstance(vector_file, (str, Path)):
            gdf = gpd.read_file(vector_file)
        elif isinstance(vector_file, gpd.GeoDataFrame):
            gdf = vector_file
        else:
            raise TypeError(f"Unsupported vector {type(vector_file)}.")
        if attr_name is None:
            gdf, attr_name = gdf.reset_index(), "index"
        if isinstance(resolution, float):
            resolution = (resolution, resolution)
        xda = make_geocube(
            gdf, measurements=[attr_name], resolution=resolution
        )[attr_name]
        return self.from_xarray(
            xda=xda,
            model=model,
            module_cls=module_cls,
            name=name,
            attr_name=attr_name,
            apply_raster=apply_raster,
            masked=masked,
            cell_cls=cell_cls,
        )

    def from_file(
        self,
        raster_file: str,
        model: MainModel[Any, Any],
        cell_cls: type[PatchCell] = PatchCell,
        module_cls: Optional[Type[PatchModule]] = None,
        name: str | None = None,
        attr_name: str | None = None,
        apply_raster: bool = False,
        band: int = 1,
        masked: bool = True,
        **kwargs: Any,
    ) -> PatchModule:
        """Create a raster layer module from a file.

        Parameters:
            raster_file:
                File path of a geo-tiff dataset.
            model:
                ABSESpy Model that the new module belongs.
            attr_name:
                Assign a attribute name to the loaded raster data.
            name:
                Name of the new module.
                If None (by default), using lowercase of the '__class__.__name__'.
                E.g., class Module -> module.
            cell_cls:
                Class type of `PatchCell` to create.

        """
        xda = rioxarray.open_rasterio(raster_file, masked=masked, **kwargs)
        xda = xda.sel(band=band)
        return self.from_xarray(
            xda=xda,
            model=model,
            module_cls=module_cls,
            name=name,
            attr_name=attr_name,
            apply_raster=apply_raster,
            masked=masked,
            cell_cls=cell_cls,
        )


class PatchModule(Module, RasterLayer):
    """Base class for managing raster-based spatial modules in ABSESpy.

    Inherits from both Module and RasterLayer to provide comprehensive spatial data management.
    Extends mesa-geo's RasterLayer with additional capabilities for:
    - Agent placement and management
    - Integration with xarray/rasterio for data I/O
    - Dynamic attribute handling
    - Spatial operations and analysis

    Attributes:
        cell_properties: Set of accessible cell attributes (decorated by @raster_attribute).
        attributes: All accessible attributes including cell_properties.
        shape2d: Raster dimensions as (height, width).
        shape3d: Raster dimensions as (1, height, width) for rasterio compatibility.
        array_cells: NumPy array of PatchCell objects.
        coords: Coordinate system dictionary with 'x' and 'y' arrays.
        random: Random selection proxy for cells.
        mask: Boolean array indicating accessible cells.
        cells_lst: ActorsList containing all cells.
        plot: Visualization interface for the module.
    """

    def __init__(
        self,
        model: MainModel[Any, Any],
        name: Optional[str] = None,
        cell_cls: Type[PatchCell] = PatchCell,
        **kwargs: Any,
    ):
        """Initializes a new PatchModule instance.

        Args:
            model: Parent model instance.
            name: Module identifier. Defaults to lowercase class name.
            cell_cls: Class to use for creating cells. Defaults to PatchCell.
            **kwargs: Additional arguments passed to RasterLayer initialization.
        """
        Module.__init__(self, model, name=name)
        RasterLayer.__init__(self, model=model, cell_cls=cell_cls, **kwargs)
        logger.info("Initializing a new Model Layer...")
        self._mask: np.ndarray = np.ones(self.shape2d).astype(bool)

    def _setup_cells(self) -> None:
        self._cells = []
        for x in range(self.width):
            col: List = []
            for y in range(self.height):
                row_idx, col_idx = self.height - y - 1, x
                col.append(
                    self.cell_cls(
                        self,
                        pos=(x, y),
                        indices=(row_idx, col_idx),
                    )
                )
            self._cells.append(col)

    @functools.cached_property
    def cells_lst(self) -> ActorsList[PatchCell]:
        """The cells stored in this layer."""
        return ActorsList(self.model, self.array_cells[self.mask])

    @property
    def mask(self) -> np.ndarray:
        """Where is not accessible."""
        return self._mask

    @mask.setter
    def mask(self, array: np.ndarray) -> None:
        """Setting mask."""
        if array.shape != self.shape2d:
            raise ABSESpyError(
                f"Shape mismatching, setting mask {array.shape}."
                f"but the module is expecting shape {self.shape2d}."
            )
        self._mask = array.astype(bool)

    def __repr__(self):
        return f"<{self.name}{self.shape2d}: {len(self.attributes)} vars>"

    @property
    def cell_properties(self) -> set[str]:
        """The accessible attributes of cells stored in this layer.
        All `PatchCell` methods decorated by `raster_attribute` should be appeared here.
        """
        return self.cell_cls.__attribute_properties__()

    @property
    def xda(self) -> xr.DataArray:
        """Get the xarray raster layer with spatial coordinates."""
        xda = xr.DataArray(data=self.mask, coords=self.coords)
        xda = xda.rio.write_crs(self.crs)
        xda = xda.rio.set_spatial_dims("x", "y")
        xda = xda.rio.write_transform(self.transform)
        return xda.rio.write_coordinate_system()

    @functools.cached_property
    def plot(self) -> _VizNature:
        """Plotting"""
        return _VizNature(self)

    @property
    def attributes(self) -> set[str]:
        """All accessible attributes from this layer."""
        return self._attributes | self.cell_properties

    @property
    def shape2d(self) -> Coordinate:
        """Raster shape in 2D (height, width).
        This is useful when working with 2d `numpy.array`.
        """
        return self.height, self.width

    @property
    def shape3d(self) -> Coordinate:
        """Raster shape in 3D (1, heigh, width).
        This is useful when working with `rasterio` band.
        """
        return 1, self.height, self.width

    @functools.cached_property
    def cells(self) -> List[List[PatchCell]]:
        """The cells stored in this layer."""
        return self._cells

    @functools.cached_property
    def array_cells(self) -> NDArray[T]:
        """Array type of the `PatchCell` stored in this module."""
        return np.flipud(np.array(self._cells, dtype=object).T)

    @property
    def coords(self) -> Coordinate:
        """Coordinate system of the raster data.

        This is useful when working with `xarray.DataArray`.
        """
        transform = self.transform
        # 注意 y 方向的分辨率通常是负值
        res_x, res_y = transform.a, -transform.e
        minx, miny, maxx, maxy = self.total_bounds
        x_coord = np.arange(minx, maxx, res_x)
        # 注意 y 坐标是从上到下递减的
        y_coord = np.flip(np.arange(miny, maxy, res_y))
        return {
            "y": y_coord,
            "x": x_coord,
        }

    def transform_coord(self, row: int, col: int) -> Coordinate:
        """Converts grid indices to real-world coordinates.

        Args:
            row: Grid row index.
            col: Grid column index.

        Returns:
            Tuple of (x, y) real-world coordinates.

        Raises:
            IndexError: If indices are out of bounds.
        """
        if self.indices_out_of_bounds(pos=(row, col)):
            raise IndexError(f"Out of bounds: {row, col}")
        return self.transform * (col, row)

    def _attr_or_array(
        self, data: None | str | np.ndarray | xr.DataArray
    ) -> np.ndarray:
        """Determine the incoming data type and turn it into a reasonable array."""
        if data is None:
            return np.ones(self.shape2d)
        if isinstance(data, xr.DataArray):
            data = data.to_numpy()
        if isinstance(data, np.ndarray):
            if data.shape == self.shape2d:
                return data
            raise ABSESpyError(
                f"Shape mismatch: {data.shape} [input] != {self.shape2d} [expected]."
            )
        if isinstance(data, str) and data in self.attributes:
            return self.get_raster(data)
        raise TypeError("Invalid data type or shape.")

    def dynamic_var(
        self,
        attr_name: str,
        dtype: Literal["numpy", "xarray"] = "numpy",
    ) -> np.ndarray:
        """Update and get dynamic variable.

        Parameters:
            attr_name:
                The dynamic variable to retrieve.

        Returns:
            2D numpy.ndarray data of the variable.
        """
        # 获取动态变量，及其附加属性
        array = super().dynamic_var(attr_name)
        assert isinstance(array, (np.ndarray, xr.DataArray, xr.Dataset))
        kwargs = super().dynamic_variables[attr_name].attrs
        # 将矩阵转换为三维，并更新空间数据
        self.apply_raster(array, attr_name=attr_name, **kwargs)
        if dtype == "numpy":
            return self.get_raster(attr_name, update=False)
        if dtype == "xarray":
            return self.get_xarray(attr_name, update=False)
        raise ValueError(f"Unknown expected dtype {dtype}.")

    def get_xarray(
        self,
        attr_name: Optional[str] = None,
        update: bool = True,
    ) -> xr.DataArray:
        """Creates an xarray DataArray representation with spatial coordinates.

        Args:
            attr_name: Attribute to retrieve. If None, returns all attributes.
            update: If True, updates dynamic variables before retrieval.

        Returns:
            xarray.DataArray with spatial coordinates and CRS information.
        """
        data = self.get_raster(attr_name=attr_name, update=update)
        if attr_name:
            name = attr_name
            data = data.reshape(self.shape2d)
            coords = self.coords
        else:
            coords = {"variable": list(self.attributes)}
            coords |= self.coords
            name = self.name
        return xr.DataArray(
            data=data,
            name=name,
            coords=coords,
        ).rio.write_crs(self.crs)

    @property
    def random(self) -> ListRandom:
        """Randomly"""
        return self.cells_lst.random

    def _select_by_geometry(
        self,
        geometry: Geometry,
        **kwargs: Dict[str, Any],
    ) -> np.ndarray:
        """Gets all the cells that intersect the given geometry.

        Parameters:
            geometry:
                Shapely Geometry to search intersected cells.
            **kwargs:
                Args pass to the function `rasterasterio.mask.mask`. It influence how to build the mask for filtering cells. Please refer [this doc](https://rasterasterio.readthedocs.io/en/latest/api/rasterasterio.mask.html) for details.

        Raises:
            ABSESpyError:
                If no available attribute exists, or the assigned refer layer is not available in the attributes.

        Returns:
            A numpy array of clipped cells.
        """
        # Return the clipped data, ensuring correct shape
        return self.xda.astype(int).rio.clip(
            [geometry], all_touched=False, drop=False, **kwargs
        )

    def select(
        self,
        where: Optional[CellFilter] = None,
    ) -> ActorsList[PatchCell]:
        """Selects cells based on specified criteria.

        Args:
            where: Selection filter. Can be:
                - None: Select all cells
                - str: Select by attribute name
                - numpy.ndarray: Boolean mask array
                - Shapely.Geometry: Select cells intersecting geometry

        Returns:
            ActorsList containing selected cells.

        Raises:
            TypeError: If where parameter is of unsupported type.

        Example:
            >>> # Select cells with elevation > 100
            >>> high_cells = module.select(module.get_raster("elevation") > 100)
            >>> # Select cells within polygon
            >>> cells = module.select(polygon)
        """
        if isinstance(where, Geometry):
            mask_ = self._select_by_geometry(geometry=where)
        elif (
            isinstance(where, (np.ndarray, str, xr.DataArray)) or where is None
        ):
            mask_ = self._attr_or_array(where).reshape(self.shape2d)
        else:
            raise TypeError(
                f"{type(where)} is not supported for selecting cells."
            )
        mask_ = np.nan_to_num(mask_, nan=0.0).astype(bool)
        return ActorsList(self.model, self.array_cells[mask_])

    sel = select

    def apply(
        self, ufunc: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> np.ndarray:
        """Apply a function to array cells.

        Parameters:
            ufunc:
                A function to apply.
            *args:
                Positional arguments to pass to the function.
            **kwargs:
                Keyword arguments to pass to the function.

        Returns:
            The result of the function applied to the array cells.
        """
        func = functools.partial(ufunc, *args, **kwargs)
        return np.vectorize(func)(self.array_cells, *args, **kwargs)

    def coord_iter(self) -> Iterator[tuple[Coordinate, PatchCell]]:
        """
        An iterator that returns coordinates as well as cell contents.
        """
        return np.ndenumerate(self.array_cells)

    def _add_attribute(
        self,
        data: np.ndarray,
        attr_name: Optional[str] = None,
        flipud: bool = False,
        apply_mask: bool = False,
    ) -> None:
        try:
            data = data.reshape(self.shape2d)
        except ValueError as e:
            raise ValueError(
                f"Data shape does not match raster shape. "
                f"Expected {self.shape2d}, received {data.shape}."
            ) from e
        if apply_mask:
            set_null_values(data, ~self.mask)
        if attr_name is None:
            attr_name = f"attribute_{len(self.attributes)}"
        self._attributes.add(attr_name)
        if flipud:
            data = np.flipud(data)
        np.vectorize(setattr)(self.array_cells, attr_name, data)

    def _add_dataarray(
        self,
        data: xr.DataArray,
        attr_name: Optional[str] = None,
        cover_crs: bool = False,
        resampling_method: str = "nearest",
        flipud: bool = False,
    ) -> None:
        if cover_crs:
            data.rio.write_crs(self.crs, inplace=True)
        resampling = getattr(Resampling, resampling_method)
        data = data.rio.reproject_match(
            self.xda,
            resampling=resampling,
        ).to_numpy()
        self._add_attribute(data, attr_name, flipud=flipud)

    def apply_raster(
        self, data: Raster, attr_name: Optional[str] = None, **kwargs: Any
    ) -> None:
        """Applies raster data to cells as attributes.

        Args:
            data: Input raster data. Can be:
                - numpy.ndarray: 2D array matching module shape
                - xarray.DataArray: With spatial coordinates
                - xarray.Dataset: With named variables
            attr_name: Name for the new attribute. Required for xarray.Dataset.
            **kwargs: Additional options:
                cover_crs: Whether to override input data CRS
                resampling_method: Method for resampling ("nearest", etc.)
                flipud: Whether to flip data vertically

        Raises:
            ValueError: If attr_name not provided for Dataset input.
            ValueError: If data shape doesn't match module shape.

        Example:
            >>> # Apply elevation data
            >>> module.apply_raster(elevation_array, attr_name="elevation")
            >>> # Apply data from xarray
            >>> module.apply_raster(xda, resampling_method="bilinear")
        """
        if isinstance(data, np.ndarray):
            self._add_attribute(data, attr_name, **kwargs)
        elif isinstance(data, xr.DataArray):
            self._add_dataarray(data, attr_name, **kwargs)
        elif isinstance(data, xr.Dataset):
            if attr_name is None:
                raise ValueError("Attribute name is required for xr.Dataset.")
            dataarray = data[attr_name]
            self._add_dataarray(dataarray, attr_name, **kwargs)

    def get_raster(
        self,
        attr_name: Optional[str] = None,
        update: bool = True,
    ) -> np.ndarray:
        """Obtaining the Raster layer by attribute.

        Parameters:
            attr_name:
                The attribute to retrieve.
                If None (by default), retrieve all attributes as a 3D array.

        Returns:
            A 3D array of attribute.
        """
        if attr_name in self.dynamic_variables and update:
            return self.dynamic_var(attr_name=attr_name).reshape(self.shape3d)
        if attr_name is not None and attr_name not in self.attributes:
            raise ValueError(
                f"Attribute {attr_name} does not exist. "
                f"Choose from {self.attributes}, or set `attr_name` to `None` to retrieve all."
            )
        if attr_name is None:
            assert bool(self.attributes), "No attribute available."
            attr_names = self.attributes
        else:
            attr_names = {attr_name}
        data = []
        for name in attr_names:
            array = np.vectorize(getattr)(self.array_cells, name)
            data.append(array)
        return np.stack(data)

    def reproject(
        self,
        xda: xr.DataArray,
        resampling: Resampling | str = "nearest",
        **kwargs,
    ) -> xr.DataArray:
        """Reproject the xarray data to the same CRS as this layer."""
        if isinstance(resampling, str):
            resampling = getattr(Resampling, resampling)
        return xda.rio.reproject_match(
            self.xda, resampling=resampling, **kwargs
        )

    def get_neighboring_cells(
        self,
        pos: Coordinate,
        moore: bool,
        include_center: bool = False,
        radius: int = 1,
    ) -> ActorsList[PatchCell]:
        """Gets neighboring cells around a position.

        Args:
            pos: Center position (x, y).
            moore: If True, uses Moore neighborhood (8 neighbors).
                  If False, uses von Neumann neighborhood (4 neighbors).
            include_center: Whether to include the center cell.
            radius: Neighborhood radius in cells.

        Returns:
            ActorsList containing neighboring cells.

        Example:
            >>> # Get Moore neighborhood with radius 2
            >>> neighbors = module.get_neighboring_cells((5,5), moore=True, radius=2)
        """
        cells = super().get_neighboring_cells(
            pos, moore, include_center, radius
        )
        return ActorsList(self.model, cells)

    @functools.lru_cache(maxsize=1000)
    def get_neighboring_by_indices(
        self,
        indices: Coordinate,
        moore: bool,
        include_center: bool = False,
        radius: int = 1,
        annular: bool = False,
    ) -> ActorsList[PatchCell]:
        """Getting neighboring positions of the given coordinate.

        Parameters:
            indices:
                The indices to get the neighborhood.
            moore:
                Whether to use Moore neighborhood.
                If False, use Von Neumann neighborhood.
            include_center:
                Whether to include the center cell.
                Default is False.
            radius:
                The radius of the neighborhood.
                Default is 1.
            annular:
                Whether to use annular (ring) neighborhood.
                Default is False.

        Returns:
            An `ActorsList` of neighboring cells.
        """
        row, col = indices
        mask_arr = np.zeros(self.shape2d, dtype=bool)
        mask_arr[row, col] = True
        mask_arr = get_buffer(
            mask_arr, radius=radius, moor=moore, annular=annular
        )
        mask_arr[row, col] = include_center
        return ActorsList(self.model, self.array_cells[mask_arr])

    def indices_out_of_bounds(self, pos: Coordinate) -> bool:
        """
        Determines whether position is off the grid.

        Parameters:
            pos: Position to check.

        Returns:
            True if position is off the grid, False otherwise.
        """

        row, col = pos
        return row < 0 or row >= self.height or col < 0 or col >= self.width
