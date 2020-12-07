def _face_can_be_removed(reference_faces, test_faces, bounding_range, pln):
    # pseudocode
    # Generate a grid of points in the bounding rect
    # for each point
    # * project onto each reference face, get min dist
    # * project onto each test face, get min dist
    # * if the min dist changes for any point between
    #   the reference and test faces, then the "POV" has
    #   changed and the face can NOT be removed

    def _gen_pts(bounding_range, pln, num_pts_per_side=12):
        pts = []
        x_min, y_min, x_max, y_max = bounding_range
        x_range = x_max - x_min
        y_range = y_max - y_min
        for ix in range(num_pts_per_side + 1):
            x = x_min + ix * x_range / num_pts_per_side
            for iy in range(num_pts_per_side + 1):
                y = y_min + iy * y_range / num_pts_per_side
                if pln == PL_XZ:
                    pts.append(gp_Pnt(x, -5, y))
                elif pln == PL_YZ:
                    pts.append(gp_Pnt(50, x, y))
                else:
                    raise RuntimeError()
        return pts

    def _get_distances(pts, faces1, faces2):
        distances1 = []
        distances2 = []
        for p in pts:
            from OCCUtils.Common import minimum_distance
            distance1 = min([minimum_distance(f, make_vertex(p))[0] for f in faces1]) if faces1 else None
            distance2 = min([minimum_distance(f, make_vertex(p))[0] for f in faces2]) if faces2 else None
            distances1.append(distance1)
            distances2.append(distance2)

        return distances1, distances2

    pts = _gen_pts(bounding_range, pln)
    for p in pts:
        display.DisplayShape(p)

    ref_distances, test_distances = _get_distances(pts, reference_faces, test_faces)
    diff = [abs(t - r) if t is not None and r is not None else 100 for t, r in zip(test_distances, ref_distances)]
    diff2 = list(filter(lambda x: x > 0.001, diff))
    # print("diff ", len(diff))
    # print("diff2 ", len(diff2))
    return len(diff2) == 0


def _remove_redundant_geometry_helper2(compound, height_mm):
    assert isinstance(compound, TopoDS_Compound)

    compound_ = copy.deepcopy(compound)
    face1_vec = gp_Vec(0, 1, 0)
    face2_vec = gp_Vec(-1, 0, 0)

    all_compound_faces = get_list_from_compound(compound_, CompoundSequenceType.FACE)
    compound_face1_nonperp_faces = get_nonperp_faces(all_compound_faces, face1_vec, False)
    compound_face2_nonperp_faces = get_nonperp_faces(all_compound_faces, face2_vec, False)

    # for cf in compound_face1_nonperp_faces:
    #     display.DisplayShape(cf, color="CYAN", transparency=0.8)
    # for cf in compound_face2_nonperp_faces:
    #     display.DisplayShape(cf, color="CYAN", transparency=0.8)

    result_compound = copy.deepcopy(compound_)
    # TODO: could iterate over perp faces only?
    all_faces = get_list_from_compound(compound_, CompoundSequenceType.FACE)

    face2_removal = []
    for index, face in enumerate(get_nonperp_faces(all_faces, face2_vec, perp=True)):
        gprop = BRepGProp_Face(face)
        normal_point = gp_Pnt(0, 0, 0)
        normal_vec = gp_Vec(0, 0, 0)
        # TODO: how to get middle of face with UV mapping?
        gprop.Normal(0, 0, normal_point, normal_vec)
        normal_vec_reversed = normal_vec.Reversed()  # point into solid
        normal_extrusion = copy.deepcopy(make_extrusion(face, 5 * height_mm, normal_vec_reversed))
        cutting_extrusion = copy.deepcopy(normal_extrusion)

        temp_cut_compound = BRepAlgoAPI_Cut(compound_, cutting_extrusion).Shape()
        reference_all_faces = get_list_from_compound(temp_cut_compound, CompoundSequenceType.FACE)
        reference_face2_nonperp_faces = get_nonperp_faces(reference_all_faces, face2_vec, False)
        yz_removal_ok = _face_can_be_removed(compound_face2_nonperp_faces, reference_face2_nonperp_faces,
                                             bounding_rect(compound_, PL_YZ), PL_YZ)
        if yz_removal_ok:
            print("cut face {}".format(index))
            face2_removal.append(copy.deepcopy(cutting_extrusion))

    face1_removal = []
    # for cf in compound_face1_nonperp_faces:
    #     display.DisplayShape(cf, color="CYAN", transparency=0.8)
    fooo = get_nonperp_faces(all_faces, face1_vec, perp=True)
    for index, face in enumerate(fooo):
        gprop = BRepGProp_Face(face)
        normal_point = gp_Pnt(0, 0, 0)
        normal_vec = gp_Vec(0, 0, 0)
        # TODO: how to get middle of face with UV mapping?
        gprop.Normal(0, 0, normal_point, normal_vec)
        normal_vec_reversed = normal_vec.Reversed()  # point into solid
        normal_extrusion = copy.deepcopy(make_extrusion(face, 5 * height_mm, normal_vec_reversed))
        cutting_extrusion = copy.deepcopy(normal_extrusion)

        temp_cut_compound = BRepAlgoAPI_Cut(compound_, cutting_extrusion).Shape()
        reference_all_faces = get_list_from_compound(temp_cut_compound, CompoundSequenceType.FACE)
        reference_face1_nonperp_faces = get_nonperp_faces(reference_all_faces, face1_vec, False)
        xz_removal_ok = _face_can_be_removed(compound_face1_nonperp_faces, reference_face1_nonperp_faces,
                                             bounding_rect(compound_, PL_XZ), PL_XZ)
        if xz_removal_ok:
            print("cut face {}".format(index))
            # display.DisplayShape(cutting_extrusion)
            face1_removal.append(copy.deepcopy(cutting_extrusion))
            # result_compound = BRepAlgoAPI_Cut(result_compound, cutting_extrusion).Shape()
    print("len face1 removal: ", len(face1_removal))
    print("len face2 removal: ", len(face2_removal))
    combo_list = [x for x in face1_removal if x in face2_removal]
    print("intersection: ", len(combo_list))

    final_shape = copy.deepcopy(compound_)
    for c in face1_removal:
        final_shape = BRepAlgoAPI_Cut(final_shape, c).Shape()
    final_shape2 = copy.deepcopy(compound_)
    for c in face2_removal:
        final_shape2 = BRepAlgoAPI_Cut(final_shape2, c).Shape()

    display.DisplayShape(final_shape)
    display.DisplayShape(final_shape2, color="WHITE")
    print("result compound")
    print(result_compound)
    start_display()
    return final_shape

    # start_display()
