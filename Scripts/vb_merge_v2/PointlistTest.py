
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


def read_vb_files_vertex_data(ib_file_index):
    """
    根据指定的Index索引，读取所有该index对应vb文件中的所有vertex-data，并组合后返回
    格式：
    vb0 - (1 - [POSITION,NORMAL,etc..])

    :param ib_file_index:
    :return:
    """
    print("开始读取vertex-data，当前索引："+str(ib_file_index))
    vb_filenames = sorted(glob.glob(ib_file_index + '-vb*txt'))

    vb_files_vertex_data = {}

    for filename in vb_filenames:
        vb_file_data_chunks = {}

        vertex_data_chunk = []
        chunk_index = None

        # Get the vb file's slot number.
        # 这里+4是因为，vb文件一般都是个位数内，一般不会是两位数
        vb_number = filename[filename.find("-vb"):filename.find("-vb") + 4][1:].encode()

        # Open the vb file.
        vb_file = open(filename, 'rb')

        # For temporarily record the last line.
        line_before_tmp = b"\r\n"

        vb_file_size = os.path.getsize(vb_file.name)
        while vb_file.tell() <= vb_file_size:
            # Read a line
            line = vb_file.readline()

            # Process vertexdata
            if line.startswith(vb_number):
                line_before_tmp = line
                vertex_data = VertexData(line)

                vertex_data_chunk.append(vertex_data)
                chunk_index = vertex_data.index

            # Process when meet the \r\n.
            if (line.startswith(b"\r\n") or vb_file.tell() == vb_file_size) and line_before_tmp.startswith(vb_number):

                line_before_tmp = b"\r\n"

                # If we got \r\n,it means this vertex_data_chunk as ended,so put it into the vb_file_data_chunks.
                vb_file_data_chunks[chunk_index] = vertex_data_chunk

                # Reset temp VertexData
                vertex_data_chunk = []

            if vb_file.tell() == vb_file_size:
                vb_files_vertex_data[vb_number] = vb_file_data_chunks
                break
        vb_file.close()

    return vb_files_vertex_data


def merge_to_vb0_vertex_data(vb_files_vertex_data):
    print("开始融合为vb0的vertex-data")
    print("接收的参数长度为：" + str(len(vb_files_vertex_data)))
    vb0_vertex_data_chunks = {}

    for vb_number in vb_files_vertex_data:
        vb_file_vertex_data_chunks = vb_files_vertex_data.get(vb_number)
        print(vb_number)
        print(len(vb_file_vertex_data_chunks))

        for index in vb_file_vertex_data_chunks:
            vertex_data_chunk = vb_file_vertex_data_chunks.get(index)

            if vb0_vertex_data_chunks.get(index) is None:
                vb0_vertex_data_chunks[index] = []
            new_vertex_data_chunk = vb0_vertex_data_chunks[index]
            for vertex_data in vertex_data_chunk:
                new_vertex_data_chunk.append(vertex_data)
            vb0_vertex_data_chunks[index] = new_vertex_data_chunk

    return vb0_vertex_data_chunks


def check_sanity_for_chunks(vb0_pointlist_vertex_data_chunks, check_texcoord=False):
    if len(vb0_pointlist_vertex_data_chunks) == 0 or vb0_pointlist_vertex_data_chunks is None:
        print("要检查的chunks不能为空")
        return None
    # 获取第一个vertex_data_chunk进行检查
    first_vertex_data_chunk = vb0_pointlist_vertex_data_chunks.get(b"0")

    # 先统计每个值出现的次数
    unique_element_value_times = {}
    for vertex_data in first_vertex_data_chunk:
        data = vertex_data.data
        if unique_element_value_times.get(data) is None:
            unique_element_value_times[data] = 1
        else:
            unique_element_value_times[data] = unique_element_value_times.get(data) + 1

    # 根据每个值出现的次数，判断该元素是否为合法的元素
    unique_element_name = []
    for vertex_data in first_vertex_data_chunk:
        data = vertex_data.data
        name = vertex_data.element_name
        if unique_element_value_times.get(data) == 1:
            unique_element_name.append(name)

    # 特别判断TEXCOORD和TEXCOORD1相同，并且值都为0,0，而被误过滤的情况
    if check_texcoord and b"TEXCOORD" not in unique_element_name:
        texcoord_data = None
        texcoord1_data = None
        for vertex_data in first_vertex_data_chunk:
            name = vertex_data.element_name
            if name == b"TEXCOORD":
                texcoord_data = vertex_data
            if name == b"TEXCOORD1":
                texcoord1_data = vertex_data
        if texcoord_data.data == texcoord1_data.data:
            unique_element_name.append(b"TEXCOORD")
            unique_element_name.append(b"TEXCOORD1")
            print("texcoord相同")


    # 根据过滤无效数据后的结果去除chunks中的无效element
    checked_vertex_data_chunks = {}
    for index in vb0_pointlist_vertex_data_chunks:
        new_vertex_data_chunk = []
        vertex_data_chunk = vb0_pointlist_vertex_data_chunks.get(index)
        for vertex_data in vertex_data_chunk:
            if vertex_data.element_name in unique_element_name:
                new_vertex_data_chunk.append(vertex_data)
        checked_vertex_data_chunks[index] = new_vertex_data_chunk

    return checked_vertex_data_chunks


def read_pointlist_vertex_data_chunks(pointlist_index):
    # 第一步，从pointlist中读取所有vb文件的vertex_data信息
    pointlist_vb_files_vertex_data = read_vb_files_vertex_data(pointlist_index)
    # print(len(pointlist_vb_files_vertex_data))

    # 第二步，把获取的pointlist的vb文件vertex_data信息融合成一个单独的dict
    vb0_pointlist_vertex_data_chunks = merge_to_vb0_vertex_data(pointlist_vb_files_vertex_data)
    # print(len(vb0_pointlist_vertex_data_chunks))

    # 第三步，抽取第一个，检查每个元素是否有问题，有问题的去掉，没问题的留下来
    checked_vertex_data_chunks = check_sanity_for_chunks(vb0_pointlist_vertex_data_chunks)

    return checked_vertex_data_chunks


def get_ib_bytes_by_indices(indices):
    ib_filenames = {}
    for index in range(len(indices)):
        indexnumber = indices[index]
        ib_filename = sorted(glob.glob(str(indexnumber) + '-ib*txt'))[0]
        ib_filenames[index] = ib_filename

    ib_bytes = {}
    for index in ib_filenames:
        ib_filename = ib_filenames.get(index)
        with open(ib_filename, "rb") as ib_file:
            bytes = ib_file.read()
            ib_bytes[index] = bytes

    return ib_bytes

def read_trianglelist_vertex_data_chunks(trianglelist_indices):

    # 首先把所有vb文件的vertex-data的chunks都读取到
    trianglelist_vb_files_chunks = {}
    for trianglelist_index in trianglelist_indices:
        # 第一步，从trianglelist中读取所有vb文件的vertex_data信息
        trianglelist_vb_files_vertex_data = read_vb_files_vertex_data(trianglelist_index)

        # 第二步，把获取的trianglelist的vb文件vertex_data信息融合成一个单独的dict
        vb0_trianglelist_vertex_data_chunks = merge_to_vb0_vertex_data(trianglelist_vb_files_vertex_data)

        # 第三步，抽取第一个，检查每个元素是否有问题，有问题的去掉，没问题的留下来
        checked_vertex_data_chunks = check_sanity_for_chunks(vb0_trianglelist_vertex_data_chunks, check_texcoord=True)

        trianglelist_vb_files_chunks[trianglelist_index] = checked_vertex_data_chunks

    # 然后把这些chunks中不合理的和重复的去掉，这里要注意，首先要根据ib获取其中内容
    ib_bytes = get_unique_ib_bytes_by_indices(trianglelist_indices)

    # TODO 这里要同时满足两个index的ib的bytes内容重复，并且vb的chunk内容也重复，才能去掉
    #   如果ib bytes相同，但vb不同，则需要根据vb具体内容来抉择去掉哪个vb，但是这种情况应该很少出现。
    #   其次，还是需要学习原神中是如何分割ib文件的，这个是非常有用的，必须得学会








def merge_pointlist_match_files(pointlist_index, trianglelist_indices, part_name):
    # 读取pointlist中存储的vertex_data_chunks
    pointlist_vertex_data_chunks = read_pointlist_vertex_data_chunks(pointlist_index)

    # 读取trianglelist中存储的vertex_data_chunks
    # 注意！trianglelist可能会出现一个indexbuffer中装载多个物体的情况









    # TODO 第二步，从trianglelist中读取COLOR,TEXCOORD,TEXCOORD1等信息
    read_trianglelist_element_list = [b"COLOR", b"TEXCOORD", b"TEXCOORD1"]

    # TODO 转化一下思路，先读取所有的vertex-data信息，然后再根据规则进行过滤，这样比较快

    #
    # final_trianglelist_vertex_data_chunk_list_list = []
    # for trianglelist_index in trianglelist_indices:
    #     vertex_data_chunk_list_tmp = read_vertex_data_chunk_list_gracefully(trianglelist_index, read_trianglelist_element_list, sanity_check=True)
    #     final_trianglelist_vertex_data_chunk_list_list.append(vertex_data_chunk_list_tmp)
    #
    # repeat_vertex_data_chunk_list_list = []
    # print("Before Sanity Check,the length is :" + str(len(final_trianglelist_vertex_data_chunk_list_list)))
    #
    # for final_trianglelist_vertex_data_chunk_list in final_trianglelist_vertex_data_chunk_list_list:
    #     first_vertex_data_chunk = final_trianglelist_vertex_data_chunk_list[0]
    #     # First,check if there have TEXCOORD, continue if not exists.
    #     element_name_list = []
    #     found_invalid_texcoord = False
    #     for vertex_data in first_vertex_data_chunk:
    #         element_name_list.append(vertex_data.element_name)
    #         datas = str(vertex_data.data.decode()).split(",")
    #         # Here > 2, because TEXCOORD's format must be R32G32_FLOAT.
    #         if vertex_data.element_name.startswith(b"TEXCOORD") and len(datas) > 2:
    #             print(datas)
    #             print("Found invalid texcoord!")
    #             found_invalid_texcoord = True
    #
    #     if found_invalid_texcoord:
    #         continue
    #
    #     if b"TEXCOORD" not in element_name_list:
    #         print("Can not found any TEXCOORD!")
    #         continue
    #
    #     for vertex_data in first_vertex_data_chunk:
    #         print(vertex_data.element_name)
    #         print(vertex_data.data)
    #     print("-----------------------------------")
    #     repeat_vertex_data_chunk_list_list.append(final_trianglelist_vertex_data_chunk_list)
    #
    # print("After Sanity Check,the length is :" + str(len(repeat_vertex_data_chunk_list_list)))
    #
    # # Remove duplicated contents.
    # final_trianglelist_vertex_data_chunk_list_list = []
    # repeat_check = []
    # for final_trianglelist_vertex_data_chunk_list in repeat_vertex_data_chunk_list_list:
    #     # Grab the first one to check.
    #     first_vertex_data_chunk = final_trianglelist_vertex_data_chunk_list[0]
    #     first_vertex_data = first_vertex_data_chunk[0]
    #
    #     # The length of final_trianglelist_vertex_data_chunk_list must equals pointlist_vertex_data_chunk_list's length.
    #     if len(final_trianglelist_vertex_data_chunk_list) == len(pointlist_vertex_data_chunk_list):
    #         if first_vertex_data.data not in repeat_check:
    #             repeat_check.append(first_vertex_data.data)
    #             final_trianglelist_vertex_data_chunk_list_list.append(final_trianglelist_vertex_data_chunk_list)
    #
    # print("vb files 去重后数量：")
    # print(len(final_trianglelist_vertex_data_chunk_list_list))
    #
    # if len(final_trianglelist_vertex_data_chunk_list_list) != 1:
    #     print("警告：The length after duplicate removal should be 1!")
    #     print("警告：当前算法默认只处理识别到的第一个！")
    #
    #
    # # TODO 这里我们添加一种情况，那就是去重后出现多个，即一个index buffer中出现多个物体
    # # After duplicate removal, there should only be one element in list,so we use index [0].
    # final_trianglelist_vertex_data_chunk_list = final_trianglelist_vertex_data_chunk_list_list[0]
    #
    # # Based on output_element_list，generate a final header_info.
    # # TODO 这里应该根据pointlist 和 trianglelist中真实存在的元素来确定到底输出哪些
    # output_element_list = [b"POSITION", b"NORMAL", b"TANGENT", b"BLENDWEIGHTS", b"BLENDINDICES", b"COLOR", b"TEXCOORD", b"TEXCOORD1"]
    #
    # header_info = get_header_info_by_elementnames(output_element_list)
    # # Set vertex count
    # header_info.vertex_count = str(len(final_trianglelist_vertex_data_chunk_list)).encode()
    #
    # # Generate a final vb file.
    # if len(pointlist_vertex_data_chunk_list) != len(final_trianglelist_vertex_data_chunk_list):
    #     print(
    #         "The length of the pointlist_vertex_data_chunk_list and the final_trianglelist_vertex_data_chunk_list should equal!")
    #     exit(1)
    #
    # final_vertex_data_chunk_list = [[] for i in range(int(str(header_info.vertex_count.decode())))]
    # for index in range(len(pointlist_vertex_data_chunk_list)):
    #     final_vertex_data_chunk_list[index] = final_vertex_data_chunk_list[index] + pointlist_vertex_data_chunk_list[
    #         index]
    #     final_vertex_data_chunk_list[index] = final_vertex_data_chunk_list[index] + \
    #                                           final_trianglelist_vertex_data_chunk_list[index]
    #
    # # Solve TEXCOORD1 can't match the element's semantic name TEXCOORD problem.
    # element_aligned_byte_offsets = {}
    # new_element_list = []
    # for element in header_info.elementlist:
    #     print("-----------------")
    #     print(element.semantic_name)
    #     print(element.semantic_index)
    #
    #     element_aligned_byte_offsets[element.semantic_name] = element.aligned_byte_offset
    #     new_element_list.append(element)
    # header_info.elementlist = new_element_list
    #
    # # Revise aligned byte offset
    # new_final_vertex_data_chunk_list = []
    # for vertex_data_chunk in final_vertex_data_chunk_list:
    #     new_vertex_data_chunk = []
    #     for vertex_data in vertex_data_chunk:
    #         # TODO 这里报错找不到TEXCOORD1
    #         vertex_data.aligned_byte_offset = element_aligned_byte_offsets[vertex_data.element_name]
    #         new_vertex_data_chunk.append(vertex_data)
    #     new_final_vertex_data_chunk_list.append(new_vertex_data_chunk)
    # final_vertex_data_chunk_list = new_final_vertex_data_chunk_list
    #
    # output_vb_fileinfo = VbFileInfo()
    # output_vb_fileinfo.header_info = header_info
    # output_vb_fileinfo.vertex_data_chunk_list = final_vertex_data_chunk_list
    #
    # ib_file_bytes = get_ib_bytes_by_indices(trianglelist_indices)
    #
    # # Output to file.
    # for index in range(len(ib_file_bytes)):
    #     ib_file_byte = ib_file_bytes[index]
    #     output_vbname = "output/" + part_name + "-vb0.txt"
    #     output_ibname = "output/" + part_name + "-ib.txt"
    #     output_vb_fileinfo.output_filename = output_vbname
    #
    #     # Write to ib file.
    #     output_ibfile = open(output_ibname, "wb+")
    #     output_ibfile.write(ib_file_byte)
    #     output_ibfile.close()
    #
    #     # Write to vb file.
    #     output_model_txt(output_vb_fileinfo)


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

            # print(pointlist_match_index)
            # print(pointlist_match)
            # print(trianglelist_indices)
            # print("----------")

            merge_pointlist_match_files(pointlist_match_index, trianglelist_indices, "part" + str(count))
            count = count + 1





