"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from NarakaMergeUtil import *




def get_pointlit_and_trianglelist_indices(input_ib_hash, root_vs, use_pointlist_tech):
    # The index number at the front of every file's filename.
    indices = sorted([re.findall('^\d+', x)[0] for x in glob.glob('*-vb0*txt')])

    pointlist_indices_dict = {}
    trianglelist_indices_dict = {}
    trianglelist_vertex_count = None
    # 1.First, grab all vb0 file's indices.
    for index in range(len(indices)):
        vb0_filename = glob.glob(indices[index] + '-vb0*txt')[0]
        topology, vertex_count = get_topology_vertexcount(vb0_filename)

        if topology == b"pointlist":
            # print("index: " + str(indices[index]) + " VertexCount = " + str(vertex_count))

            # Filter, vb0 filename must have ROOT VS.
            if use_pointlist_tech:
                if root_vs in vb0_filename:
                    pointlist_indices_dict[indices[index]] = vertex_count
            else:
                pointlist_indices_dict[indices[index]] = vertex_count

        ib_filename = glob.glob(indices[index] + '-ib*txt')[0]
        topology, vertex_count = get_topology_vertexcount(ib_filename)
        if topology == b"trianglelist":
            # Filter,ib filename must include input_ib_hash.
            if input_ib_hash in ib_filename:
                topology, vertex_count = get_topology_vertexcount(vb0_filename)
                trianglelist_indices_dict[(indices[index])] = vertex_count
                trianglelist_vertex_count = vertex_count

    # Based on vertex count, remove the duplicated pointlist indices.
    pointlist_indices = []
    trianglelist_indices = []
    for pointlist_index in pointlist_indices_dict:
        if pointlist_indices_dict.get(pointlist_index) == trianglelist_vertex_count:
            pointlist_indices.append(pointlist_index)

    for trianglelist_index in trianglelist_indices_dict:
        trianglelist_indices.append(trianglelist_index)

    print("----------------------------------------------------------")
    print("Pointlist vb indices: " + str(pointlist_indices))
    print("Trianglelist vb indices: " + str(trianglelist_indices))

    return pointlist_indices, trianglelist_indices


def output_pointlist_ini_file(pointlist_indices, input_ib_hash, part_name):
    print("Start to output ini file.")
    filenames = sorted(glob.glob(pointlist_indices[0] + '-vb*txt'))
    position_vb = filenames[0]
    position_vb = position_vb[position_vb.find("-vb0=") + 5:position_vb.find("-vs=")]

    texcoord_vb = filenames[1]
    texcoord_vb = texcoord_vb[texcoord_vb.find("-vb1=") + 5:texcoord_vb.find("-vs=")]

    blend_vb = filenames[2]
    blend_vb = blend_vb[blend_vb.find("-vb2=") + 5:blend_vb.find("-vs=")]

    # print("position_vb: " + position_vb)
    # print("texcoord_vb: " + texcoord_vb)
    # print("blend_vb: " + blend_vb)

    output_bytes = b""
    output_bytes = output_bytes + (b"[Resource_POSITION]\r\ntype = Buffer\r\nstride = 40\r\nfilename = " + part_name.encode() + b"_POSITION.buf\r\n\r\n")
    output_bytes = output_bytes + (b"[Resource_BLEND]\r\ntype = Buffer\r\nstride = 32\r\nfilename = " + part_name.encode() + b"_BLEND.buf\r\n\r\n")
    output_bytes = output_bytes + (b"[Resource_TEXCOORD]\r\ntype = Buffer\r\nstride = 8\r\nfilename = " + part_name.encode() + b"_TEXCOORD.buf\r\n\r\n")
    output_bytes = output_bytes + (b"[Resource_IB_FILE]\r\ntype = Buffer\r\nformat = DXGI_FORMAT_R16_UINT\r\nfilename = " + part_name.encode() + b".ib\r\n\r\n")
    output_bytes = output_bytes + (b"[Resource_"+part_name.encode() + b"]\r\nfilename = "+ part_name.encode()+b".png\r\n\r\n")

    output_bytes = output_bytes + (b"[TextureOverride_IB_SKIP]\r\nhash = "+input_ib_hash.encode()+b"\r\nhandling = skip\r\nib = Resource_IB_FILE\r\n;ps-t7 = Resource_"+ part_name.encode()+b"\r\ndrawindexed = auto\r\n\r\n")
    output_bytes = output_bytes + (b"[TextureOverride_POSITION]\r\nhash = "+position_vb.encode()+b"\r\nvb0 = Resource_POSITION\r\n\r\n")
    output_bytes = output_bytes + (b"[TextureOverride_TEXCOORD]\r\nhash = "+texcoord_vb.encode()+b"\r\nvb1 = Resource_TEXCOORD\r\n\r\n")
    output_bytes = output_bytes + (b"[TextureOverride_BLEND]\r\nhash = "+blend_vb.encode()+b"\r\nvb2 = Resource_BLEND\r\n\r\n")
    output_bytes = output_bytes + (b";[TextureOverride_VB_SKIP_1]\r\n;hash = \r\n;handling = skip\r\n\r\n")

    output_file = open("output/"+part_name+".ini", "wb+")
    output_file.write(output_bytes)
    output_file.close()


def output_trianglelist_ini_file(pointlist_indices, input_ib_hash, part_name):
    print("Start to output ini file.")
    filenames = sorted(glob.glob(pointlist_indices[0] + '-vb*txt'))
    position_vb = filenames[0]
    position_vb = position_vb[position_vb.find("-vb0=") + 5:position_vb.find("-vs=")]

    texcoord_vb = filenames[1]
    texcoord_vb = texcoord_vb[texcoord_vb.find("-vb1=") + 5:texcoord_vb.find("-vs=")]


    print("position_vb: " + position_vb)
    print("texcoord_vb: " + texcoord_vb)


    output_bytes = b""
    output_bytes = output_bytes + (b"[Resource_POSITION]\r\ntype = Buffer\r\nstride = 40\r\nfilename = " + part_name.encode() + b"_POSITION.buf\r\n\r\n")
    output_bytes = output_bytes + (b"[Resource_TEXCOORD]\r\ntype = Buffer\r\nstride = 8\r\nfilename = " + part_name.encode() + b"_TEXCOORD.buf\r\n\r\n")
    output_bytes = output_bytes + (b"[Resource_IB_FILE]\r\ntype = Buffer\r\nformat = DXGI_FORMAT_R16_UINT\r\nfilename = " + part_name.encode() + b".ib\r\n\r\n")
    output_bytes = output_bytes + (b"[Resource_"+part_name.encode() + b"]\r\nfilename = "+ part_name.encode()+b".png\r\n\r\n")

    output_bytes = output_bytes + (b"[TextureOverride_IB_SKIP]\r\nhash = "+input_ib_hash.encode()+b"\r\nhandling = skip\r\nib = Resource_IB_FILE\r\n;ps-t7 = Resource_"+ part_name.encode()+b"\r\ndrawindexed = auto\r\n\r\n")
    output_bytes = output_bytes + (b"[TextureOverride_POSITION]\r\nhash = "+position_vb.encode()+b"\r\nvb0 = Resource_POSITION\r\n\r\n")
    output_bytes = output_bytes + (b"[TextureOverride_TEXCOORD]\r\nhash = "+texcoord_vb.encode()+b"\r\nvb1 = Resource_TEXCOORD\r\n\r\n")
    output_bytes = output_bytes + (b";[TextureOverride_VB_SKIP_1]\r\n;hash = \r\n;handling = skip\r\n\r\n")

    output_file = open("output/"+part_name+".ini", "wb+")
    output_file.write(output_bytes)
    output_file.close()


def merge_pointlist_files(pointlist_indices, trianglelist_indices, part_name):
    move_related_files(trianglelist_indices, move_dds=True, only_pst7=True)

    output_pointlist_ini_file(pointlist_indices, input_ib_hash, part_name)

    # The vertex data you want to read from pointlist vb file.
    read_pointlist_element_list = [b"POSITION", b"NORMAL", b"TANGENT", b"BLENDWEIGHTS", b"BLENDINDICES"]

    pointlist_vertex_data_chunk_list = read_vertex_data_chunk_list_gracefully(pointlist_indices[0],
                                                                              read_pointlist_element_list)

    # The vertex data you want to read from trianglelist vb file.
    read_trianglelist_element_list = [b"COLOR", b"TEXCOORD", b"TEXCOORD1"]

    final_trianglelist_vertex_data_chunk_list_list = []
    for trianglelist_index in trianglelist_indices:
        vertex_data_chunk_list_tmp = read_vertex_data_chunk_list_gracefully(trianglelist_index,
                                                                            read_trianglelist_element_list,
                                                                            only_vb1=True, sanity_check=True)
        final_trianglelist_vertex_data_chunk_list_list.append(vertex_data_chunk_list_tmp)

    repeat_vertex_data_chunk_list_list = []

    for final_trianglelist_vertex_data_chunk_list in final_trianglelist_vertex_data_chunk_list_list:
        first_vertex_data_chunk = final_trianglelist_vertex_data_chunk_list[0]
        # First,check if there have TEXCOORD, continue if not exists.
        element_name_list = []
        found_invalid_texcoord = False
        for vertex_data in first_vertex_data_chunk:
            element_name_list.append(vertex_data.element_name)
            datas = str(vertex_data.data.decode()).split(",")
            # Here > 2, because TEXCOORD's format must be R32G32_FLOAT.
            if vertex_data.element_name.startswith(b"TEXCOORD") and len(datas) > 2:
                found_invalid_texcoord = True

        if found_invalid_texcoord:
            continue

        if b"TEXCOORD" not in element_name_list:
            continue

        # for vertex_data in first_vertex_data_chunk:
        #     print(vertex_data.element_name)
        #     print(vertex_data.data)
        # print("-----------------------------------")
        repeat_vertex_data_chunk_list_list.append(final_trianglelist_vertex_data_chunk_list)

    # Remove duplicated contents.
    final_trianglelist_vertex_data_chunk_list_list = []
    repeat_check = []
    for final_trianglelist_vertex_data_chunk_list in repeat_vertex_data_chunk_list_list:
        # Grab the first one to check.
        first_vertex_data_chunk = final_trianglelist_vertex_data_chunk_list[0]
        first_vertex_data = first_vertex_data_chunk[0]

        # The length of final_trianglelist_vertex_data_chunk_list must equals pointlist_vertex_data_chunk_list's length.
        if len(final_trianglelist_vertex_data_chunk_list) == len(pointlist_vertex_data_chunk_list):
            if first_vertex_data.data not in repeat_check:
                repeat_check.append(first_vertex_data.data)
                final_trianglelist_vertex_data_chunk_list_list.append(final_trianglelist_vertex_data_chunk_list)

    if len(final_trianglelist_vertex_data_chunk_list_list) != 1:
        print("The length after duplicate removal should be 1!")
        exit(1)

    # After duplicate removal, there should only be one element in list,so we use index [0].
    final_trianglelist_vertex_data_chunk_list = final_trianglelist_vertex_data_chunk_list_list[0]

    # Based on output_element_list，generate a final header_info.
    # TODO 这里应该根据pointlist 和 trianglelist中真实存在的元素来确定到底输出哪些
    output_element_list = [b"POSITION", b"NORMAL", b"TANGENT", b"BLENDWEIGHTS", b"BLENDINDICES", b"COLOR", b"TEXCOORD", b"TEXCOORD1"]

    header_info = get_header_info_by_elementnames(output_element_list)
    # Set vertex count
    header_info.vertex_count = str(len(final_trianglelist_vertex_data_chunk_list)).encode()

    # Generate a final vb file.
    if len(pointlist_vertex_data_chunk_list) != len(final_trianglelist_vertex_data_chunk_list):
        print(
            "The length of the pointlist_vertex_data_chunk_list and the final_trianglelist_vertex_data_chunk_list should equal!")
        exit(1)

    final_vertex_data_chunk_list = [[] for i in range(int(str(header_info.vertex_count.decode())))]
    for index in range(len(pointlist_vertex_data_chunk_list)):
        final_vertex_data_chunk_list[index] = final_vertex_data_chunk_list[index] + pointlist_vertex_data_chunk_list[
            index]
        final_vertex_data_chunk_list[index] = final_vertex_data_chunk_list[index] + \
                                              final_trianglelist_vertex_data_chunk_list[index]

    # Solve TEXCOORD1 can't match the element's semantic name TEXCOORD problem.
    element_aligned_byte_offsets = {}
    new_element_list = []
    for element in header_info.elementlist:
        print("-----------------")
        print(element.semantic_name)
        print(element.semantic_index)

        element_aligned_byte_offsets[element.semantic_name] = element.aligned_byte_offset
        new_element_list.append(element)
    header_info.elementlist = new_element_list

    # Revise aligned byte offset
    new_final_vertex_data_chunk_list = []
    for vertex_data_chunk in final_vertex_data_chunk_list:
        new_vertex_data_chunk = []
        for vertex_data in vertex_data_chunk:
            # TODO 这里报错找不到TEXCOORD1
            vertex_data.aligned_byte_offset = element_aligned_byte_offsets[vertex_data.element_name]
            new_vertex_data_chunk.append(vertex_data)
        new_final_vertex_data_chunk_list.append(new_vertex_data_chunk)
    final_vertex_data_chunk_list = new_final_vertex_data_chunk_list

    output_vb_fileinfo = VbFileInfo()
    output_vb_fileinfo.header_info = header_info
    output_vb_fileinfo.vertex_data_chunk_list = final_vertex_data_chunk_list

    ib_file_bytes = get_unique_ib_bytes_by_indices(trianglelist_indices)

    # Output to file.
    for index in range(len(ib_file_bytes)):
        ib_file_byte = ib_file_bytes[index]
        output_vbname = "output/" + input_ib_hash + "-" + part_name + "-vb0.txt"
        output_ibname = "output/" + input_ib_hash + "-" + part_name + "-ib.txt"
        output_vb_fileinfo.output_filename = output_vbname

        # Write to ib file.
        output_ibfile = open(output_ibname, "wb+")
        output_ibfile.write(ib_file_byte)
        output_ibfile.close()

        # Write to vb file.
        output_model_txt(output_vb_fileinfo)


def merge_trianglelist_files(trianglelist_indices, part_name):
    output_element_list = [b"POSITION", b"NORMAL", b"TANGENT", b"TEXCOORD"]

    move_related_files(trianglelist_indices, move_dds=True, only_pst7=True)

    # The vertex data you want to read from trianglelist vb file.
    read_trianglelist_element_list = [b"POSITION", b"NORMAL", b"TANGENT", b"TEXCOORD"]

    # Read all the trianglelist indices.
    final_trianglelist_vertex_data_chunk_list_list = []
    for trianglelist_index in trianglelist_indices:
        vertex_data_chunk_list_tmp = read_vertex_data_chunk_list_gracefully(trianglelist_index, read_trianglelist_element_list, only_vb1=False, sanity_check=True)
        final_trianglelist_vertex_data_chunk_list_list.append(vertex_data_chunk_list_tmp)

    # Final output index
    final_output_indices = []

    # Remove the invalid file content.
    repeat_vertex_data_chunk_list_list = []
    count = 0
    for final_trianglelist_vertex_data_chunk_list in final_trianglelist_vertex_data_chunk_list_list:
        first_vertex_data_chunk = final_trianglelist_vertex_data_chunk_list[0]

        # First,check if there have TEXCOORD, continue if not exists.
        element_name_list = []
        found_invalid_texcoord = False
        for vertex_data in first_vertex_data_chunk:
            element_name_list.append(vertex_data.element_name)
            datas = str(vertex_data.data.decode()).split(",")
            # Here > 2, because TEXCOORD's format must be R32G32_FLOAT.
            if vertex_data.element_name.startswith(b"TEXCOORD") and len(datas) > 2:
                found_invalid_texcoord = True
        if found_invalid_texcoord:
            continue

        # Must have at least one TEXCOORD
        if b"TEXCOORD" not in element_name_list:
            continue

        # for vertex_data in first_vertex_data_chunk:
        #     print(vertex_data.element_name)
        #     print(vertex_data.data)
        # print("-----------------------------------")
        repeat_vertex_data_chunk_list_list.append(final_trianglelist_vertex_data_chunk_list)
        final_output_indices.append(trianglelist_indices[count])
        count = count + 1

    # print(final_output_indices)

    new_final_output_indices = []
    count = 0

    # Remove duplicated contents.
    final_trianglelist_vertex_data_chunk_list_list = []
    repeat_check = []
    for final_trianglelist_vertex_data_chunk_list in repeat_vertex_data_chunk_list_list:
        # Grab the first one to check.
        first_vertex_data_chunk = final_trianglelist_vertex_data_chunk_list[0]
        first_vertex_data = first_vertex_data_chunk[0]
        # 校验元素个数，必须和指定要输出的元素列表的元素个数相同
        if len(first_vertex_data_chunk) != len(output_element_list):
            count = count + 1
            continue

        if first_vertex_data.data not in repeat_check:
            repeat_check.append(first_vertex_data.data)
            final_trianglelist_vertex_data_chunk_list_list.append(final_trianglelist_vertex_data_chunk_list)
            new_final_output_indices.append(final_output_indices[count])
            count = count + 1

    print(new_final_output_indices)
    if len(final_trianglelist_vertex_data_chunk_list_list) != 1:
        print("The length after duplicate removal should be 1!")
        exit(1)

    # After duplicate removal, there should only be one element in list,so we use index [0].
    final_trianglelist_vertex_data_chunk_list = final_trianglelist_vertex_data_chunk_list_list[0]

    # Based on output_element_list，generate a final header_info.
    header_info = get_header_info_by_elementnames(output_element_list)
    # Set vertex count
    header_info.vertex_count = str(len(final_trianglelist_vertex_data_chunk_list)).encode()

    # Generate a final vb file.
    final_vertex_data_chunk_list = [[] for i in range(int(str(header_info.vertex_count.decode())))]
    for index in range(len(final_trianglelist_vertex_data_chunk_list)):
        final_vertex_data_chunk_list[index] = final_vertex_data_chunk_list[index] + final_trianglelist_vertex_data_chunk_list[index]

    # Solve TEXCOORD1 can't match the element's semantic name TEXCOORD problem.
    element_aligned_byte_offsets = {}
    new_element_list = []
    for element in header_info.elementlist:
        element_aligned_byte_offsets[element.semantic_name] = element.aligned_byte_offset
        if element.semantic_name.endswith(b"TEXCOORD1"):
            element.semantic_name = b"TEXCOORD"
        new_element_list.append(element)
    header_info.elementlist = new_element_list

    # Revise aligned byte offset
    new_final_vertex_data_chunk_list = []
    for vertex_data_chunk in final_vertex_data_chunk_list:
        new_vertex_data_chunk = []
        for vertex_data in vertex_data_chunk:
            vertex_data.aligned_byte_offset = element_aligned_byte_offsets[vertex_data.element_name]
            new_vertex_data_chunk.append(vertex_data)
        new_final_vertex_data_chunk_list.append(new_vertex_data_chunk)
    final_vertex_data_chunk_list = new_final_vertex_data_chunk_list

    output_vb_fileinfo = VbFileInfo()
    output_vb_fileinfo.header_info = header_info
    output_vb_fileinfo.vertex_data_chunk_list = final_vertex_data_chunk_list

    ib_file_bytes = get_unique_ib_bytes_by_indices(trianglelist_indices)

    # Output to file.
    for index in range(len(ib_file_bytes)):
        ib_file_byte = ib_file_bytes[index]
        output_vbname = "output/" + input_ib_hash + "-" + part_name + "-vb0.txt"
        output_ibname = "output/" + input_ib_hash + "-" + part_name + "-ib.txt"
        output_vb_fileinfo.output_filename = output_vbname

        # Write to ib file.
        output_ibfile = open(output_ibname, "wb+")
        output_ibfile.write(ib_file_byte)
        output_ibfile.close()

        # Write to vb file.
        output_model_txt(output_vb_fileinfo)
        # Finally, output ini file.
    output_trianglelist_ini_file(final_output_indices, input_ib_hash, part_name)




def start_merge_files(input_ib_hash, part_name, root_vs, use_pointlist_tech, force_pointlist_index=None):
    """

    :param input_ib_hash: the index buffer hash you want to extract.
    :param part_name: set a name for this ib part.
    :param root_vs: if a game use pointlist tech,it's animation will load in root_vs.
    :param use_pointlist_tech: True or False, if true,use pointlist tech,if not,use trianglelist tech only.
    :param force_pointlist_index: if multiple pointlist file appears,you can force to use a special pointlist file index.
    :return:
    """
    pointlist_indices, trianglelist_indices = get_pointlit_and_trianglelist_indices(input_ib_hash, root_vs, use_pointlist_tech=use_pointlist_tech)

    if use_pointlist_tech:

        if len(pointlist_indices) == 0:
            print("Can't found any pointlist file,please turn pointlist tech flag to False for ['" + part_name + "']")
            exit(1)

        merge_pointlist_files(pointlist_indices, trianglelist_indices, part_name)
    else:
        print("Only fetch from trianglelist files.")
        merge_trianglelist_files(trianglelist_indices, part_name)



if __name__ == "__main__":
    # Here is the ROOT VS the game currently use, Naraka use e8425f64cfb887cd as it's ROOT VS now.
    # and this value is different between games which use pointlist topology.
    NarakaRootVS = "e8425f64cfb887cd"
    # Here is your Loader location.
    NarakaLoaderFolder = "C:/Users/Administrator/Desktop/NarakaLoaderV1.1/"

    # Set work dir, here is your FrameAnalysis dump dir.
    NarakaFrameAnalyseFolder = "FrameAnalysis-2023-02-21-154750"
    # Here is the ib you want to import into blender.
    naraka_ib_hashs = {"c46735f7": ["cloth", True], "0ccb9a46": ["body", True]}

    os.chdir(NarakaLoaderFolder + NarakaFrameAnalyseFolder + "/")
    if not os.path.exists('output'):
        os.mkdir('output')

    for input_ib_hash in naraka_ib_hashs:
        ib_hash_property = naraka_ib_hashs.get(input_ib_hash)
        name = ib_hash_property[0]
        use_pointlist_tech = ib_hash_property[1]
        start_merge_files(input_ib_hash, name, root_vs=NarakaRootVS, use_pointlist_tech=use_pointlist_tech)
    print("----------------------------------------------------------\r\nAll process done！")
    # TODO 目前测试发现，不使用pointlist技术的衣服部位，由于缺少Blend信息，无法正确地导入游戏中
    #  但是这种的如果直接去掉，却会导致某个地方露个大洞，很烦人，目前ib导入肯定没问题，TEXCOORD也没问题，关键在于POSITION放在哪个hash里才能正确的加载
    #  而且对于武器这种没有使用pointlist的，到底该如何导入才能正确？否则岂不是无法实现武器替换，去原神看看是怎么实现的
    #  原神中转而使用了其它的pointlist，即使对应不上，他说存在对应不上的情况
    #  那我就去原神里面看看，角色的武器什么的用的是不是pointlist

    # TODO add a variable to specify output folder.
    # TODO solve the vertex limit problem,
    #  because we can't correctly replace a object which vertex number is more than original object.


