
SET(SCRIPT
  ../../scripts/WaveSystemPStag/WaveSystemPStag.py
  )

FILE(GLOB MY_MESHES_AND_PICTURES  "../../../ressources/2DDeformedQuadrangles/squareWithDeformedQuadrangles_*" )

file(COPY ${SCRIPT} ${MY_MESHES_AND_PICTURES} DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
install(FILES ${SCRIPT} ${MY_MESHES_AND_PICTURES} DESTINATION share/validation/test_validation2DWaveSystemPStagDeformedQuadrangles)

if (CDMATH_WITH_PYTHON AND CDMATH_WITH_PETSC AND CDMATH_WITH_POSTPRO)

    SET(BCTYPE  Wall  )

    SET(SCALING  2  )

    ADD_TEST(validationWaveSystem_2DFV_PStag_deformedQuadrangles ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/test_validation2DWaveSystemPStagDeformedQuadrangles.py ${BCTYPE} ${SCALING})
endif (CDMATH_WITH_PYTHON AND CDMATH_WITH_PETSC AND CDMATH_WITH_POSTPRO)


