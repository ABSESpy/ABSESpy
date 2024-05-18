#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""PatchModule class
"""
from __future__ import annotations

import copy
import functools
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterator,
    Literal,
    Optional,
    Sequence,
    Set,
    Type,
    Union,
    cast,
    overload,
)

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

import numpy as np
import pyproj
import rasterio
import rioxarray
import xarray as xr
from loguru import logger
from mesa.space import Coordinate
from mesa_geo.raster_layers import RasterBase
from rasterio import mask
from rasterio.enums import Resampling
from rasterio.warp import calculate_default_transform, transform_bounds
from shapely import Geometry

from abses._bases.errors import ABSESpyError
from abses._bases.modules import Module, _ModuleFactory
from abses.cells import PatchCell
from abses.random import ListRandom
from abses.sequences import ActorsList
from abses.tools.func import get_buffer, set_null_values
from abses.viz.viz_nature import _VizNature

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
        to_create = cast(PatchModule, self._check_cls(module_cls=module_cls))
        xda = rioxarray.open_rasterio(raster_file, masked=masked, **kwargs)
        xda = xda.sel(band=band)
        obj: PatchModule = to_create(
            model=model,
            name=name,
            width=xda.rio.width,
            height=xda.rio.height,
            crs=xda.rio.crs,
            total_bounds=xda.rio.bounds(),
            cell_cls=cell_cls,
        )
        if masked:
            obj.mask = xda.notnull().to_numpy()
        if apply_raster:
            obj.apply_raster(xda, attr_name=attr_name, **kwargs)
        return obj


class PatchModule(Module, RasterBase):
    """
    The spatial sub-module base class.
    Inherit from this class to create a submodule.
    [This tutorial](../tutorial/beginner/organize_model_structure.ipynb) shows the model structure.
    This is also a raster layer, inherited from the 'mesa-geo.RasterLayer' class.
    ABSESpy extends this class, so it can:
    1. place agents (by `_CellAgentsContainer` class.)
    2. work with `xarray`, `rasterio` packages for better data I/O workflow.

    Attributes:
        cell_properties:
            The accessible attributes of cells stored in this layer.
            When a `PatchCell`'s method is decorated by `raster_attribute`,
            it should be appeared here as a property attribute.
        attributes:
            All accessible attributes from this layer,
            including cell_properties.
        shape2d:
            Raster shape in 2D (heigh, width).
        shape3d:
            Raster shape in 3D (1, heigh, width),
            this is for compatibility with `mg.RasterLayer` and `rasterio`.
        array_cells:
            Array type of the `PatchCell` stored in this module.
        coords:
            Coordinate system of the raster data.
            This is useful when working with `xarray.DataArray`.
        random:
            A random proxy by calling the cells as an `ActorsList`.
    """

    def __init__(
        self,
        model: MainModel[Any, Any],
        name: Optional[str] = None,
        cell_cls: Type[PatchCell] = PatchCell,
        **kwargs: Any,
    ):
        """This method copied some of the `mesa-geo.RasterLayer`'s methods."""
        Module.__init__(self, model, name=name)
        RasterBase.__init__(self, **kwargs)
        self.cell_cls = cell_cls
        logger.info("Initializing a new Model Layer...")
        logger.info(f"Using rioxarray version: {rioxarray.__version__}")

        func = np.vectorize(lambda row, col: cell_cls(self, (row, col)))
        self._cells: np.ndarray = np.fromfunction(
            func, shape=(self.height, self.width), dtype=object
        )
        self._attributes: Set[str] = set()
        self.mask: np.ndarray = np.ones(self.shape2d)

    @functools.cached_property
    def cells(self) -> ActorsList[PatchCell]:
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

    def __getitem__(
        self,
        index: int | Sequence[Coordinate] | tuple[int | slice, int | slice],
    ) -> PatchCell | list[PatchCell]:
        """
        Access contents from the grid.
        """
        return self.array_cells.__getitem__(index)

    def __iter__(self) -> Iterator[PatchCell]:
        """
        Create an iterator that chains the rows of the cells together
        as if it is one list
        """
        for row in self.array_cells:
            yield from row

    @property
    def cell_properties(self) -> set[str]:
        """The accessible attributes of cells stored in this layer.
        All `PatchCell` methods decorated by `raster_attribute` should be appeared here.
        """
        return self.cell_cls.__attribute_properties__()

    @functools.cached_property
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
    def array_cells(self) -> np.ndarray:
        """Array type of the `PatchCell` stored in this module."""
        return self._cells

    @property
    def coords(self) -> Coordinate:
        """Coordinate system of the raster data.

        This is useful when working with `xarray.DataArray`.
        """
        nrows, ncols = self.shape2d
        coords_x = np.arange(ncols) * self.transform[0] + self.transform[2]
        coords_y = np.arange(nrows) * self.transform[4] + self.transform[5]
        return {
            "y": coords_y,
            "x": coords_x,
        }

    def transform_coord(self, row: int, col: int) -> Coordinate:
        """Transforming the row, col to the real-world coordinate."""
        if self.out_of_bounds(pos=(row, col)):
            raise IndexError(f"Out of bounds: {row, col}")
        return self.transform * (col, row)

    def to_crs(self, crs, inplace=False) -> Optional[PatchModule]:
        """Converting the raster data to a another CRS."""
        super()._to_crs_check(crs)
        layer = self if inplace else copy.copy(self)

        src_crs = rasterio.crs.CRS.from_user_input(layer.crs)
        dst_crs = rasterio.crs.CRS.from_user_input(crs)
        if not layer.crs.is_exact_same(crs):
            transform, _, _ = calculate_default_transform(
                src_crs,
                dst_crs,
                self.width,
                self.height,
                *layer.total_bounds,
            )
            layer.total_bounds = [
                *transform_bounds(src_crs, dst_crs, *layer.total_bounds)
            ]
            layer.crs = crs
            layer.transform = transform

        return None if inplace else layer

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
        dtype: Literal["numpy", "xarray", "rasterio"] = "numpy",
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
        if dtype == "rasterio":
            return self.get_rasterio(attr_name, update=False)
        raise ValueError(f"Unknown expected dtype {dtype}.")

    def get_rasterio(
        self,
        attr_name: Optional[str] = None,
        update: bool = True,
    ) -> rasterio.MemoryFile:
        """Gets the Rasterio raster layer corresponding to the attribute. Save to a temporary rasterio memory file.

        Parameters:
            attr_name:
                The attribute name for creating the rasterio file.

        Returns:
            The rasterio tmp memory file of raster.
        """
        if attr_name is None:
            data = np.ones(self.shape2d)
        else:
            data = self.get_raster(attr_name=attr_name, update=update)
        # 如果获取到的是2维，重整为3维
        if len(data.shape) != 3:
            data = data.reshape(self.shape3d)
        with rasterio.MemoryFile() as mem_file:
            with mem_file.open(
                driver="GTiff",
                height=data.shape[1],
                width=data.shape[2],
                count=data.shape[0],  # number of bands
                dtype=str(data.dtype),
                crs=self.crs,
                transform=self.transform,
            ) as dataset:
                dataset.write(data)
            # Open the dataset again for reading and return
            return mem_file.open()

    def get_xarray(
        self,
        attr_name: Optional[str] = None,
        update: bool = True,
    ) -> xr.DataArray:
        """Get the xarray raster layer with spatial coordinates.

        Parameters:
            attr_name:
                The attribute to retrieve. If None (by default),
                return all available attributes (3D DataArray).
                Otherwise, 2D DataArray of the chosen attribute.

        Returns:
            Xarray.DataArray data with spatial coordinates of the chosen attribute.
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
        return self.cells.random

    def _select_by_geometry(
        self,
        geometry: Geometry,
        refer_layer: Optional[str] = None,
        **kwargs: Dict[str, Any],
    ) -> np.ndarray:
        """Gets all the cells that intersect the given geometry.

        Parameters:
            geometry:
                Shapely Geometry to search intersected cells.
            refer_layer:
                The attribute name to refer when filtering cells.
            **kwargs:
                Args pass to the function `rasterasterio.mask.mask`. It influence how to build the mask for filtering cells. Please refer [this doc](https://rasterasterio.readthedocs.io/en/latest/api/rasterasterio.mask.html) for details.

        Raises:
            ABSESpyError:
                If no available attribute exists, or the assigned refer layer is not available in the attributes.

        Returns:
            A list of PatchCell.
        """
        if refer_layer is not None and refer_layer not in self.attributes:
            raise ABSESpyError(
                f"The refer layer {refer_layer} is not available in the attributes"
            )
        data = self.get_rasterio(attr_name=refer_layer)
        out_image, _ = mask.mask(data, [geometry], **kwargs)
        return out_image.reshape(self.shape2d)

    def select(
        self,
        where: Optional[CellFilter] = None,
    ) -> ActorsList[PatchCell]:
        """Select cells from this layer.
        Also has a shortcut alias for this method: `.sel`.

        Parameters:
            where:
                The condition to select cells.
                If None (by default), select all cells.
                If a string, select cells by the attribute name.
                If a numpy.ndarray, select cells by the mask array.
                If a Shapely Geometry, select cells by the intersection with the geometry.

        Raises:
            TypeError:
                If the input type is not supported.

        Returns:
            An `ActorsList` with all selected cells stored.
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
        mask_ = np.nan_to_num(mask_, nan=0.0).astype(bool) & self.mask
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
        self, data: Raster, attr_name: Optional[str], **kwargs: Any
    ) -> None:
        """Apply raster data to the cells.

        Parameters:
            data:
                np.ndarray data: 2D numpy array with shape (1, height, width).
                xr.DataArray data: xarray DataArray with spatial coordinates.
                xr.Dataset data: xarray Dataset with spatial coordinates.
            attr_name:
                Name of the attribute to be added to the cells.
                If None, a random name will be generated.
                Default is None.
            **kwargs:
                cover_crs:
                    Whether to cover the crs of the input data.
                    If False, it assumes the input data has crs info.
                    If True, it will cover the crs of the input data by the crs of this layer.
                    Default is False.
                resampling_method:
                    The [resampling method](https://rasterio.readthedocs.io/en/stable/api/rasterio.enums.html#rasterio.enums.Resampling)
                    when re-projecting the input data.
                    Default is "nearest".
                flipud:
                    Whether to flip the input data upside down.
                    Set to True when the input data is not in the same direction as the raster layer.
                    Default is False.
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

    @overload
    def get_neighborhood(
        self,
        pos: Coordinate,
        moore: bool,
        include_center: bool = False,
        radius: int = 1,
        annular: bool = False,
        return_mask: bool = True,
    ) -> np.ndarray:
        ...

    @functools.lru_cache(maxsize=1000)
    def get_neighborhood(
        self,
        pos: Coordinate,
        moore: bool,
        include_center: bool = False,
        radius: int = 1,
        annular: bool = False,
        return_mask: bool = False,
    ) -> ActorsList[PatchCell] | np.ndarray:
        """Getting neighboring positions of the given coordinate.

        Parameters:
            pos:
                The coordinate to get the neighborhood.
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
            return_mask:
                Whether to return a mask array.
                If True, return a mask array of the neighboring locations.
                Otherwise, return a `ActorsList` of neighboring cells.
                Default is False.

        Returns:
            An `ActorsList` of neighboring cells, or a mask array.
            Where the mask array is a boolean array with the same shape as the raster layer.
            The True value indicates the cell is in the neighborhood.
        """
        mask_arr = np.zeros(self.shape2d, dtype=bool)
        mask_arr[pos[0], pos[1]] = True
        mask_arr = get_buffer(
            mask_arr, radius=radius, moor=moore, annular=annular
        )
        mask_arr[pos[0], pos[1]] = include_center
        if return_mask:
            return mask_arr
        return ActorsList(self.model, self.array_cells[mask_arr])

    def to_file(
        self,
        raster_file: str,
        attr_name: Optional[str] = None,
        driver: str = "GTiff",
    ) -> None:
        """
        Writes a raster layer to a file.

        Parameters:
            raster_file:
                The path to the raster file to write to.
            attr_name:
                The name of the attribute to write to the raster.
                If None, all attributes are written. Default is None.
            driver:
                The GDAL driver to use for writing the raster file.
                Default is 'GTiff'.
                See GDAL docs at https://gdal.org/drivers/raster/index.html.
        """

        data = self.get_raster(attr_name)
        with rasterio.open(
            raster_file,
            "w",
            driver=driver,
            width=self.width,
            height=self.height,
            count=data.shape[0],
            dtype=data.dtype,
            crs=self.crs,
            transform=self.transform,
        ) as dataset:
            dataset.write(data)

    def out_of_bounds(self, pos: Coordinate) -> bool:
        """
        Determines whether position is off the grid.

        Parameters:
            pos: Position to check.

        Returns:
            True if position is off the grid, False otherwise.
        """

        row, col = pos
        return row < 0 or row >= self.height or col < 0 or col >= self.width
