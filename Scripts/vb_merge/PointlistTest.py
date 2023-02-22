
from NarakaMergeUtil import *


# TODO 如果使用了pointlist技术，则正确的位置信息应该存储在pointlist中
#  在遇到不使用pointlist技术的物体，又无法获取正确的blend时，只能把所有的pointlist的POSITION、NORMAL、TANGENT组合起来放入blender里看看，
#  到底哪个对应了人物的身体部分，但是有可能这个衣服部位只是固定在了身体的某个地方，默认不会发生变化，所以不需要专门存储blend信息
#  我猜想是剩余的部件共用了一个pointlist，所以vertex count匹配不上，只要把所有剩余部件vertex count值加起来，便能得到对应pointlist
#  或者干脆把所有pointlist列举出来后，一一和trianglelist对比，并读取到blender，直接查看所有的内容。

# TODO 第一步，获取所有的pointlist index

def get_all_pointlist_trianglelist_index():
    # The index number at the front of every file's filename.
    indices = sorted([re.findall('^\d+', x)[0] for x in glob.glob('*-vb0*txt')])

    pointlist_indices_dict = {}
    trianglelist_indices_dict = {}
    # 1.First, grab all vb0 file's indices.
    for index in range(len(indices)):
        vb0_filename = glob.glob(indices[index] + '-vb0*txt')[0]
        topology, vertex_count = get_topology_vertexcount(vb0_filename)

        if topology == b"pointlist":
            pointlist_indices_dict[indices[index]] = vertex_count

        if topology == b"trianglelist":
            trianglelist_indices_dict[(indices[index])] = vertex_count

    print("Pointlist vb indices: " + str(pointlist_indices_dict))
    print("共"+ str(len(pointlist_indices_dict)) +"个")
    print("Trianglelist vb indices: " + str(trianglelist_indices_dict))
    print("共"+ str(len(trianglelist_indices_dict)) +"个")

    return pointlist_indices_dict,trianglelist_indices_dict


def match_by_vertex_count(pointlist_indices_dict={},trianglelist_indices_dict={}):

    pointlist_match_dict = {}

    for pointlist_index in pointlist_indices_dict:
        pointlist_vertex_count = pointlist_indices_dict.get(pointlist_index)

        found_trianglelist = {}

        for trianglelist_index in trianglelist_indices_dict:
            trianglelist_vertex_count = trianglelist_indices_dict.get(trianglelist_index)

            if pointlist_vertex_count == trianglelist_vertex_count:
                found_trianglelist[trianglelist_index] = trianglelist_vertex_count

        pointlist_match_dict[pointlist_index] = found_trianglelist

    for pointlist_match_index in pointlist_match_dict:
        print("pointlist index: " + str(pointlist_match_index) + "  pointlist vertex count: " + str(pointlist_indices_dict.get(pointlist_match_index)))
        print("match trianglelist: " + str(pointlist_match_dict.get(pointlist_match_index)))
        print("--------------")

    return pointlist_match_dict


def merge_pointlist_match_files(pointlist_index, trianglelist_indices, part_name):
    move_related_files(trianglelist_indices, move_dds=True, only_pst7=True)

    # output_pointlist_ini_file(pointlist_indices, input_ib_hash, part_name)

    # The vertex data you want to read from pointlist vb file.
    read_pointlist_element_list = [b"POSITION", b"NORMAL", b"TANGENT", b"BLENDWEIGHTS", b"BLENDINDICES"]

    pointlist_vertex_data_chunk_list = read_vertex_data_chunk_list_gracefully(pointlist_index,
                                                                              read_pointlist_element_list)

    # The vertex data you want to read from trianglelist vb file.
    read_trianglelist_element_list = [b"COLOR", b"TEXCOORD", b"TEXCOORD1"]

    final_trianglelist_vertex_data_chunk_list_list = []
    for trianglelist_index in trianglelist_indices:
        vertex_data_chunk_list_tmp = read_vertex_data_chunk_list_gracefully(trianglelist_index, read_trianglelist_element_list, sanity_check=True)
        final_trianglelist_vertex_data_chunk_list_list.append(vertex_data_chunk_list_tmp)

    repeat_vertex_data_chunk_list_list = []
    print("Before Sanity Check,the length is :" + str(len(final_trianglelist_vertex_data_chunk_list_list)))

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
                print(datas)
                print("Found invalid texcoord!")
                found_invalid_texcoord = True

        if found_invalid_texcoord:
            continue

        if b"TEXCOORD" not in element_name_list:
            print("Can not found any TEXCOORD!")
            continue

        for vertex_data in first_vertex_data_chunk:
            print(vertex_data.element_name)
            print(vertex_data.data)
        print("-----------------------------------")
        repeat_vertex_data_chunk_list_list.append(final_trianglelist_vertex_data_chunk_list)

    print("After Sanity Check,the length is :" + str(len(repeat_vertex_data_chunk_list_list)))

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

    print("vb files 去重后数量：")
    print(len(final_trianglelist_vertex_data_chunk_list_list))

    if len(final_trianglelist_vertex_data_chunk_list_list) != 1:
        print("警告：The length after duplicate removal should be 1!")
        print("警告：当前算法默认只处理识别到的第一个！")


    # TODO 这里我们添加一种情况，那就是去重后出现多个，即一个index buffer中出现多个物体
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

    ib_file_bytes = get_ib_bytes_by_indices(trianglelist_indices)

    # Output to file.
    for index in range(len(ib_file_bytes)):
        ib_file_byte = ib_file_bytes[index]
        output_vbname = "output/" + part_name + "-vb0.txt"
        output_ibname = "output/" + part_name + "-ib.txt"
        output_vb_fileinfo.output_filename = output_vbname

        # Write to ib file.
        output_ibfile = open(output_ibname, "wb+")
        output_ibfile.write(ib_file_byte)
        output_ibfile.close()

        # Write to vb file.
        output_model_txt(output_vb_fileinfo)


if __name__ == "__main__":
    # Here is the ROOT VS the game currently use, Naraka use e8425f64cfb887cd as it's ROOT VS now.
    # and this value is different between games which use pointlist topology.
    NarakaRootVS = "e8425f64cfb887cd"
    # Here is your Loader location.
    NarakaLoaderFolder = "C:/Users/Administrator/Desktop/NarakaLoaderV1.1/"

    # Set work dir, here is your FrameAnalysis dump dir.
    NarakaFrameAnalyseFolder = "FrameAnalysis-2023-02-22-150707"

    os.chdir(NarakaLoaderFolder + NarakaFrameAnalyseFolder + "/")
    if not os.path.exists('output'):
        os.mkdir('output')

    print("----------------------------------------------------------")
    print("开始读取所有pointlist和trianglelist的index：")
    pointlist_indices_dict,trianglelist_indices_dict = get_all_pointlist_trianglelist_index()

    print("----------------------------------------------------------")
    print("开始对每个pointlist和trianglelist做vertex_count匹配")
    pointlist_match_dict = match_by_vertex_count(pointlist_indices_dict,trianglelist_indices_dict)

    print("----------------------------------------------------------")
    print("开始对每个pointlist匹配到的物体做融合输出")
    count = 0
    for pointlist_match_index in pointlist_match_dict:
        pointlist_match = pointlist_match_dict.get(pointlist_match_index)

        if len(pointlist_match) > 0:
            trianglelist_indices = []

            for trianglelist_index in pointlist_match:
                trianglelist_indices.append(trianglelist_index)

            print(pointlist_match_index)
            print(pointlist_match)
            print(trianglelist_indices)
            print("----------")
            #
            # merge_pointlist_match_files(pointlist_match_index, trianglelist_indices, "part" + str(count))
            # count = count + 1





