
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
    # print("开始读取vertex-data，当前索引："+str(ib_file_index))
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
    # print("开始融合为vb0的vertex-data")
    # print("接收的参数长度为：" + str(len(vb_files_vertex_data)))
    vb0_vertex_data_chunks = {}

    for vb_number in vb_files_vertex_data:
        vb_file_vertex_data_chunks = vb_files_vertex_data.get(vb_number)
        # print(vb_number)
        # print(len(vb_file_vertex_data_chunks))

        for index in vb_file_vertex_data_chunks:
            vertex_data_chunk = vb_file_vertex_data_chunks.get(index)

            if vb0_vertex_data_chunks.get(index) is None:
                vb0_vertex_data_chunks[index] = []
            new_vertex_data_chunk = vb0_vertex_data_chunks[index]
            for vertex_data in vertex_data_chunk:
                new_vertex_data_chunk.append(vertex_data)
            vb0_vertex_data_chunks[index] = new_vertex_data_chunk

    return vb0_vertex_data_chunks


def check_sanity_for_chunks(vb0_pointlist_vertex_data_chunks, retain_duplicated_texcoord=False):
    if len(vb0_pointlist_vertex_data_chunks) == 0 or vb0_pointlist_vertex_data_chunks is None:
        raise NameError("要检查的chunks不能为空")

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
    if retain_duplicated_texcoord and b"TEXCOORD" not in unique_element_name:
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
            print("texcoord相同,全部加入，待后续定夺")

    # 根据过滤无效数据后的结果去除chunks中的无效element的vertex-data
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
    print("开始读取pointlist：")

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
        ib_filenames[indexnumber] = ib_filename

    ib_bytes = {}
    for index in ib_filenames:
        ib_filename = ib_filenames.get(index)
        with open(ib_filename, "rb") as ib_file:
            bytes = ib_file.read()
            ib_bytes[index] = bytes

    return ib_bytes


def read_trianglelist_vertex_data_chunks(trianglelist_indices, read_element_list=None):
    print("开始读取trianglelist：")

    # 首先把所有vb文件的vertex-data的chunks都读取到
    trianglelist_vb_files_chunks = {}
    for trianglelist_index in trianglelist_indices:
        # 第一步，从trianglelist中读取所有vb文件的vertex_data信息
        trianglelist_vb_files_vertex_data = read_vb_files_vertex_data(trianglelist_index)

        # 第二步，把获取的trianglelist的vb文件vertex_data信息融合成一个单独的dict
        vb0_trianglelist_vertex_data_chunks = merge_to_vb0_vertex_data(trianglelist_vb_files_vertex_data)

        # 第三步，抽取第一个，检查每个元素是否有问题，有问题的去掉，没问题的留下来
        checked_vertex_data_chunks = check_sanity_for_chunks(vb0_trianglelist_vertex_data_chunks, retain_duplicated_texcoord=False)

        trianglelist_vb_files_chunks[trianglelist_index] = checked_vertex_data_chunks

    # 然后把这些chunks中不合理的和重复的去掉，这里要注意，首先要根据ib获取其中内容
    ib_bytes = get_ib_bytes_by_indices(trianglelist_indices)

    # 整合，方便后续处理
    ib_vb_file_candidates = {}
    for index in ib_bytes:
        # print(index)
        ib_byte = ib_bytes.get(index)
        vb_file_chunks = trianglelist_vb_files_chunks.get(index)
        if ib_vb_file_candidates.get(ib_byte) is None:
            ib_vb_file_candidates[ib_byte] = [vb_file_chunks]
        else:
            vb_file_chunks_list = ib_vb_file_candidates.get(ib_byte)
            vb_file_chunks_list.append(vb_file_chunks)
            ib_vb_file_candidates[ib_byte] = vb_file_chunks_list

    # 过滤，首先必须包含TEXCOORD，且所有TEXCOORD格式必须正确
    new_ib_vb_file_candidates = {}
    for ib_byte in ib_vb_file_candidates:
        vb_file_chunks_list = ib_vb_file_candidates.get(ib_byte)
        new_vb_file_chunks_list = []
        for vb_file_chunks in vb_file_chunks_list:
            first_vertex_data_chunk = vb_file_chunks.get(b"0")

            # 首先判断是否含有TEXCOORD
            element_name_list = []
            found_invalid_texcoord = False
            for vertex_data in first_vertex_data_chunk:
                element_name_list.append(vertex_data.element_name)
                datas = str(vertex_data.data.decode()).split(",")
                # Here > 2, because TEXCOORD's format must be R32G32_FLOAT.
                if vertex_data.element_name.startswith(b"TEXCOORD") and len(datas) > 2:
                    # print(datas)
                    # print("Found invalid texcoord!")
                    found_invalid_texcoord = True

            if found_invalid_texcoord:
                continue

            if b"TEXCOORD" not in element_name_list:
                # print("Can not find any TEXCOORD!")
                continue

            # for vertex_data in first_vertex_data_chunk:
            #     print(vertex_data.element_name)
            #     print(vertex_data.data)
            # print("-----------------------------------")
            new_vb_file_chunks_list.append(vb_file_chunks)

        # 只保留需要保留的element,如不指定，默认只读取TEXCOORD和TEXCOORD1
        if read_element_list is None:
            read_element_list = [b"TEXCOORD", b"TEXCOORD1"]

        retain_vb_file_chunks_list = []
        for vb_file_chunks in new_vb_file_chunks_list:
            new_vb_file_chunks = {}
            for index in vb_file_chunks:
                vertex_data_chunk = vb_file_chunks.get(index)
                new_vertex_data_chunk = []
                for vertex_data in vertex_data_chunk:
                    element_name = vertex_data.element_name
                    if element_name in read_element_list:
                        new_vertex_data_chunk.append(vertex_data)
                new_vb_file_chunks[index] = new_vertex_data_chunk
            retain_vb_file_chunks_list.append(new_vb_file_chunks)



        # 然后对new_vb_file_chunks_list进行去重
        # print("去重前：" + str(len(retain_vb_file_chunks_list)))
        unique_chunk = []
        unique_vb_file_chunks_list = []
        for vb_file_chunks in retain_vb_file_chunks_list:
            first_vertex_data_chunk = vb_file_chunks.get(b"0")

            first_data_str = b""
            for vertex_data in first_vertex_data_chunk:
                first_data_str = first_data_str + vertex_data.data

            if first_data_str not in unique_chunk:
                unique_chunk.append(first_data_str)
                unique_vb_file_chunks_list.append(vb_file_chunks)

        # print("去重后：" + str(len(unique_vb_file_chunks_list)))
        #  去重后，可能会出现一些文件只有TEXCOORD，一些文件却有TEXCOORD和TEXCOORD1的情况
        #  所以默认要保留元素更多的那个，尤其是readelementlist为TEXCOORD和TEXCOORD1的情况
        if read_element_list == [b"TEXCOORD", b"TEXCOORD1"]:
            new_unique_vb_file_chunks_list = []
            for vb_file_chunks in unique_vb_file_chunks_list:
                if len(vb_file_chunks) == len(read_element_list):
                    new_unique_vb_file_chunks_list.append(vb_file_chunks)

            unique_vb_file_chunks_list = new_unique_vb_file_chunks_list

        new_ib_vb_file_candidates[ib_byte] = unique_vb_file_chunks_list

    # 格式检查，去重后必须每个ib_bytes都只有唯一的一个vb_file_chunks_list对应，不能出现多个
    for ib_byte in new_ib_vb_file_candidates:
        vb_file_chunks_list = new_ib_vb_file_candidates.get(ib_byte)
        if len(vb_file_chunks_list) > 1:
            raise NameError("错误！trianglelist去重后应只有一个")

    print("读取完毕，ib文件数量：" + str(len(new_ib_vb_file_candidates)))











def merge_pointlist_match_files(pointlist_index, trianglelist_indices, part_name):
    print("当前处理索引：" + str(pointlist_index))
    print("对应trianglelist indices：" + str(trianglelist_indices))
    # 读取pointlist中存储的vertex_data_chunks
    pointlist_vertex_data_chunks = read_pointlist_vertex_data_chunks(pointlist_index)

    # 读取trianglelist中存储的vertex_data_chunks
    # 注意！trianglelist可能会出现一个indexbuffer中装载多个物体的情况
    trianglelist_vertex_data_chunks = read_trianglelist_vertex_data_chunks(trianglelist_indices)


def view_all_pointlist_in_blender(pointlist_indices_dict):
    for pointlist_index in pointlist_indices_dict:
        # 读取pointlist中存储的vertex_data_chunks
        pointlist_vertex_data_chunks = read_pointlist_vertex_data_chunks(pointlist_index)

        # 保留以下元素
        output_element_list = [b"POSITION", b"NORMAL", b"TANGENT", b"TEXCOORD", b"TEXCOORD1"]

        # 读取headerinfo
        header_info = get_header_info_by_elementnames(output_element_list)

        # Set vertex count
        header_info.vertex_count = str(len(pointlist_vertex_data_chunks)).encode()

        # 设置topology为trianglelist，因为pointlist里面的默认是pointlist无法被读取
        header_info.topology = b"trianglelist"

        # Solve TEXCOORD1 can't match the element's semantic name TEXCOORD problem.
        # 给element_list设置正确的索引偏移量
        element_aligned_byte_offsets = {}
        new_element_list = []
        for element in header_info.elementlist:
            # print("-----------------")
            # print(element.semantic_name)
            # print(element.semantic_index)
            element_aligned_byte_offsets[element.semantic_name] = element.aligned_byte_offset
            new_element_list.append(element)
        header_info.elementlist = new_element_list

        # 输出elementlist看一下
        for element in new_element_list:
            print(element.semantic_name)
            print(element.aligned_byte_offset)
        print("-----------------------------")
        # TODO 保留部分Vertex-data元素

        # TODO 重新设置所有vertex-data 中对应的alygned_byte_offset

        # TODO 输出IB文件

        # TODO 对每一个IB文件都输出对应的VB文件


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

    print("所有pointlist处理完成")


if __name__ == "__main__":
    # TODO 新增指定输出目录，这样融合脚本的输出和分割脚本的输入就可以作为最终的mod文件夹了。

    # Here is the ROOT VS the game currently use, Naraka use e8425f64cfb887cd as it's ROOT VS now.
    # and this value is different between games which use pointlist topology.
    NarakaRootVS = "e8425f64cfb887cd"
    # Here is your Loader location.
    NarakaLoaderFolder = "C:/Users/Administrator/Desktop/NBLoaderV1.1/"

    # Set work dir, here is your FrameAnalysis dump dir.
    NarakaFrameAnalyseFolder = "FrameAnalysis-2023-03-02-132041"

    os.chdir(NarakaLoaderFolder + NarakaFrameAnalyseFolder + "/")
    if not os.path.exists('output'):
        os.mkdir('output')

    print("----------------------------------------------------------")
    print("开始读取所有pointlist和trianglelist的index：")
    pointlist_indices_dict,trianglelist_indices_dict = get_all_pointlist_trianglelist_index()

    # TODO 非常重要，这里会将所有的pointlist的vb中的POSITION、NORMAL、TANGENT组合成为一个可以导入到blender中的vb文件
    #  然后我们就可以去blender中查看所有的pointlist所对应的物体了
    view_all_pointlist_in_blender(pointlist_indices_dict)





    # print("----------------------------------------------------------")
    # print("开始对每个pointlist和trianglelist做vertex_count匹配")
    # pointlist_match_dict = match_by_vertex_count(pointlist_indices_dict,trianglelist_indices_dict)
    #
    # print("----------------------------------------------------------")
    # print("开始对每个pointlist匹配到的物体做融合输出")
    # count = 0
    # for pointlist_match_index in pointlist_match_dict:
    #     pointlist_match = pointlist_match_dict.get(pointlist_match_index)
    #
    #     if len(pointlist_match) > 0:
    #         trianglelist_indices = []
    #
    #         for trianglelist_index in pointlist_match:
    #             trianglelist_indices.append(trianglelist_index)
    #
    #         # print(pointlist_match_index)
    #         # print(pointlist_match)
    #         # print(trianglelist_indices)
    #         # print("----------")
    #
    #         merge_pointlist_match_files(pointlist_match_index, trianglelist_indices, "part" + str(count))
    #         count = count + 1





