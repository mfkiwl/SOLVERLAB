cmake_minimum_required (VERSION 3.1)
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Project name
project (CDMATH)
set (CDMATH_VERSION_MAJOR 9)
set (CDMATH_VERSION_MINOR 13)

# CDMATH project options (deprecated, see SOLVERLAB options)
set (CDMATH_WITH_PETSC ${SOLVERLAB_WITH_PETSC} CACHE STRING "Compile CDMATH with PETSc linking")
set (CDMATH_WITH_DOCUMENTATION ${SOLVERLAB_WITH_DOCUMENTATION} CACHE STRING "Generate documentation with doxygen")
set (CDMATH_WITH_PYTHON ${SOLVERLAB_WITH_PYTHON} CACHE STRING "Compile Python interface for CDMATH")
set (CDMATH_WITH_POSTPRO ${SOLVERLAB_WITH_POSTPRO} CACHE STRING "Install postprocessing Python modules")
set (CDMATH_WITH_PACKAGE ${SOLVERLAB_WITH_PACKAGE} CACHE STRING "Generate RPM, Debian and tarball packages")
set (CDMATH_WITH_TESTS ${SOLVERLAB_WITH_TESTS} CACHE STRING "Compile unit testing")

#Path to installed libraries
set (PETSC_DIR            OFF CACHE STRING "PETSc library path" )
set (SLEPC_DIR            OFF CACHE STRING "SLEPc library path" )
set (F2CBLASLAPACK_DIR    OFF CACHE STRING "F2CBLASLAPACK library path" )
set (HDF5_ROOT            OFF CACHE STRING "HDF5 library path" )#For the compilation of MED with a specific version of HDF5
set (MEDFILE_ROOT_DIR     OFF CACHE STRING "MED library path" )
set (MEDCOUPLING_ROOT_DIR OFF CACHE STRING "MEDCoupling library path" )

set (DOWNLOAD_PETSC         https://ftp.mcs.anl.gov/pub/petsc/release-snapshots/petsc-3.21.0.tar.gz
     CACHE STRING           "PETSc tarball path/url" )
set (DOWNLOAD_SLEPC         https://slepc.upv.es/download/distrib/slepc-3.21.0.tar.gz
     CACHE STRING           "SLEPC tarball path/url" )
set (DOWNLOAD_F2CBLASLAPACK https://www.mcs.anl.gov/petsc/mirror/externalpackages/f2cblaslapack-3.8.0.q2.tar.gz
     CACHE STRING           "F2CBLASLAPACK tarball path/url" )
set (DOWNLOAD_HDF5          https://support.hdfgroup.org/ftp/HDF5/releases/hdf5-1.10/hdf5-1.10.3/src/hdf5-1.10.3.tar.gz
     CACHE STRING           "HDF5 tarball path/url" )
set (GIT_MED                http://git.salome-platform.org/gitpub/modules/med.git
     CACHE STRING           "MED git repository")
set (GIT_MEDCOUPLING        http://git.salome-platform.org/gitpub/tools/medcoupling.git
     CACHE STRING           "MEDCoupling git repository" )
set (GIT_CONFIGURATION        http://git.salome-platform.org/gitpub/tools/configuration.git
     CACHE STRING           "CONFIGURATION git repository" )


# Base directories
set (BASE_DIR ${CDMATH_SOURCE_DIR}/base)
set (MESH_DIR ${CDMATH_SOURCE_DIR}/mesh)
set (LINEARSOLVER_DIR ${CDMATH_SOURCE_DIR}/linearsolver)
set (CDMATH_SWIG_DIR ${CDMATH_SOURCE_DIR}/swig)
set (CDMATH_POSTPRO_DIR ${CDMATH_SOURCE_DIR}/postprocessing)

set (TESTS_DIR ${CDMATH_SOURCE_DIR}/tests)

###Define CDMATH_INCLUDES and CDMATH_LIBRARIES for the compilation of CoreFlows
set(CDMATH_INCLUDES 
	${MEDFILE_INCLUDE_DIRS} ${MEDCOUPLING_INCLUDE_DIR}
	${BASE_DIR}/inc ${MESH_DIR}/inc ${LINEARSOLVER_DIR}/inc 
	PARENT_SCOPE 	)

set (CDMATH_LIBRARIES
	medC medloader	medcoupling
	base mesh 	linearsolver
	PARENT_SCOPE    )
 
# Swig interface
if   (CDMATH_WITH_PYTHON)
  set (CPACK_DEBIAN_PACKAGE_DEPENDS "${CPACK_DEBIAN_PACKAGE_DEPENDS}, python-dev, python-numpy, swig")
  set (CPACK_RPM_PACKAGE_REQUIRES   "${CPACK_RPM_PACKAGE_REQUIRES},   python-devel,      numpy, swig")
  add_subdirectory (${CDMATH_SWIG_DIR})
endif(CDMATH_WITH_PYTHON)

add_subdirectory (${BASE_DIR})
add_subdirectory (${MESH_DIR})

if   (CDMATH_WITH_PETSC)
    add_subdirectory (${LINEARSOLVER_DIR})
endif(CDMATH_WITH_PETSC)

# Documentation
if (CDMATH_WITH_DOCUMENTATION)
  configure_file (Doxyfile.in ${PROJECT_BINARY_DIR}/Doxyfile  @ONLY IMMEDIATE)
  add_custom_target (docCDMATH COMMAND ${DOXYGEN_EXECUTABLE} ${PROJECT_BINARY_DIR}/Doxyfile SOURCES ${PROJECT_BINARY_DIR}/Doxyfile)
  if   ( IS_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/doc/html)
    install(DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/doc/html DESTINATION share/doc/cdmath-dev-doc)
  endif( IS_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/doc/html)
endif(CDMATH_WITH_DOCUMENTATION)

#Debug option : todo = sort flags
if   (CMAKE_BUILD_TYPE STREQUAL "Debug")
  SET(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -pg -fprofile-arcs -ftest-coverage -lgcov")
  SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -pg -fprofile-arcs -ftest-coverage -lgcov")
endif(CMAKE_BUILD_TYPE STREQUAL "Debug")

# Tests
if   (CDMATH_WITH_TESTS)
  enable_testing ()
  add_subdirectory (${TESTS_DIR})#contains c++ and python tests
endif(CDMATH_WITH_TESTS)

# Packaging
if (CDMATH_WITH_PACKAGE)
  include (${CDMATH_SOURCE_DIR}/CPackLists.txt)
endif(CDMATH_WITH_PACKAGE)

# Postprocessing
if (CDMATH_WITH_PYTHON AND CDMATH_WITH_POSTPRO)
  add_subdirectory (postprocessing)
endif ()

# Configuration file
configure_file(
    ${PROJECT_SOURCE_DIR}/env_CDMATH.sh
    @ONLY
)
													    

