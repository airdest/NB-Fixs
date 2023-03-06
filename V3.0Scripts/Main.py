import os
import re
import glob
import shutil
from DataStructure import *


def get_topology_vertexcount(filename):
    ib_file = open(filename, "rb")
    ib_file_size = os.path.getsize(filename)
    get_topology = None
    get_vertex_count = None
    count = 0
    while ib_file.tell() <= ib_file_size:
        line = ib_file.readline()
        # Because topology only appear in the first 5 line,so if count > 5 ,we can stop looking for it.
        count = count + 1
        if count > 5:
            break
        if line.startswith(b"vertex count: "):
            get_vertex_count = line[line.find(b"vertex count: ") + b"vertex count: ".__len__():line.find(b"\r\n")]

        if line.startswith(b"topology: "):
            topology = line[line.find(b"topology: ") + b"topology: ".__len__():line.find(b"\r\n")]
            if topology == b"pointlist":
                get_topology = b"pointlist"
                break
            if topology == b"trianglelist":
                get_topology = b"trianglelist"
                break

    # Safely close the file.
    ib_file.close()

    return get_topology, get_vertex_count


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

    return pointlist_indices_dict, trianglelist_indices_dict


def read_vb_files_vertex_data(ib_file_index, only_vb0=False):
    # print("开始读取vertex-data，当前索引："+str(ib_file_index))
    if only_vb0:
        vb_filenames = sorted(glob.glob(ib_file_index + '-vb0*txt'))
    else:
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


def output_model_txt(vb_file_info):
    # TODO 需重写此方法
    #  默认认为所有的elementlist和vertex-data都已经全部处理正确，在这里只需要直接输出
    #  接收到的element_list和vertex-data中的element必须正确对应
    header_info = vb_file_info.header_info
    vb0_vertex_data = vb_file_info.vb0_vertex_data
    output_filename = vb_file_info.output_filename

    print("Starting output to file: " + output_filename)

    # Output to the final file.
    output_file = open(output_filename, "wb+")

    # (1) First, output header.
    output_file.write(b"stride: " + header_info.stride + b"\r\n")
    output_file.write(b"first vertex: " + header_info.first_vertex + b"\r\n")
    output_file.write(b"vertex count: " + header_info.vertex_count + b"\r\n")
    output_file.write(b"topology: " + header_info.topology + b"\r\n")

    # (2) Second, output element list
    element_list = header_info.elementlist
    for element in element_list:
        element_name = element.semantic_name
        semantic_index = element.semantic_index
        if element_name == b"TEXCOORD":
            if semantic_index != b'0':
                element_name = element_name + semantic_index

        # print("Detected："+str(element_name))
        # Output the corroesponding element.
        output_file.write(b"element[" + element.element_number + b"]:" + b"\r\n")
        output_file.write(b"  SemanticName: " + element.semantic_name + b"\r\n")
        output_file.write(b"  SemanticIndex: " + element.semantic_index + b"\r\n")
        output_file.write(b"  Format: " + element.format + b"\r\n")
        output_file.write(b"  InputSlot: " + element.input_slot + b"\r\n")
        output_file.write(b"  AlignedByteOffset: " + element.aligned_byte_offset + b"\r\n")
        output_file.write(b"  InputSlotClass: " + element.input_slot_class + b"\r\n")
        output_file.write(b"  InstanceDataStepRate: " + element.instance_data_step_rate + b"\r\n")

    # (3) Write the vertex-data part.
    output_file.write(b"\r\n")
    output_file.write(b"vertex-data:\r\n")
    output_file.write(b"\r\n")

    # (4) output vertex-data
    for index in vb0_vertex_data:
        vertex_data_list = vb0_vertex_data.get(index)
        for vertex_data in vertex_data_list:
            output_file.write(vertex_data.__str__())

        # If it is the final line ,we don't append \r\n.
        if index != len(vb0_vertex_data) - 1:
            output_file.write(b"\r\n")

    output_file.close()


if __name__ == "__main__":
    # TODO 新增指定输出目录，这样融合脚本的输出和分割脚本的输入就可以作为最终的mod文件夹了。
    #  用1.0脚本分析原神dump文件，和原神的脚本做对比，拆解分析原神脚本思路
    #  新增一个方法：pointlist和trianglelist配对后只输出配对成功的

    # Here is the ROOT VS the game currently use, Naraka use e8425f64cfb887cd as it's ROOT VS now.
    # and this value is different between games which use pointlist topology.
    NarakaRootVS = "e8425f64cfb887cd"

    # Here is your Loader location.
    NarakaLoaderFolder = "C:/Users/Administrator/Desktop/GenshinLoader/"

    # Set work dir, here is your FrameAnalysis dump dir.
    NarakaFrameAnalyseFolder = "FrameAnalysis-2023-03-06-135256"

    os.chdir(NarakaLoaderFolder + NarakaFrameAnalyseFolder + "/")
    if not os.path.exists('output'):
        os.mkdir('output')

    print("----------------------------------------------------------------------------------")
    print("开始读取所有pointlist和trianglelist的index：")
    pointlist_indices_dict, trianglelist_indices_dict = get_all_pointlist_trianglelist_index()
    # print(pointlist_indices_dict)
    """
    此处输出格式为：
    {'000001': b'1126', '000002': b'523'}
    key为索引，value为vb文件的vertex-count
    """

    print("----------------------------------------------------------------------------------")
    print("移动所有ib文件到output目录")
    for index in pointlist_indices_dict:
        filename = glob.glob(str(index)+'-ib*.txt')[0]
        print("Moving ： " + filename + " ....")
        shutil.copy2(filename, 'output/' + filename)

    print("----------------------------------------------------------------------------------")
    print("读取pointlist的index列表中所有vb0的POSITION、NORMAL、TANGENT信息")
    for index in pointlist_indices_dict:
        retain_element_list = [b"POSITION", b"NORMAL", b"TANGENT"]
        print("读取对应的vb0的element_list信息")
        # 读取headerinfo
        header_info = get_header_info_by_elementnames(retain_element_list)

        # Set vertex count
        header_info.vertex_count = pointlist_indices_dict.get(index)

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

        # 读取vb0文件的vertex_data
        vb0_vertex_data = read_vb_files_vertex_data(index, only_vb0=True).get(b"vb0")
        # print(output)
        # print(output.__len__()) 只读取vb0的话，这里应该为1
        """
        这里的输出格式为：
        {
        b'vb0': {b'0': [<DataStructure.VertexData object at 0x000002287F9950D0>  , <DataStructure.VertexData object at 0x000002287F9C4390>], 
                b'1': [<DataStructure.VertexData object at 0x000002287F9C43D0>, <DataStructure.VertexData object at 0x000002287F9C45D0>]
                .....},
        b'vb1': {b'0': [<DataStructure.VertexData object at 0x000002287F9950D0>  , <DataStructure.VertexData object at 0x000002287F9C4390>], 
                b'1': [<DataStructure.VertexData object at 0x000002287F9C43D0>, <DataStructure.VertexData object at 0x000002287F9C45D0>]
                .....}
        }
        """
        print("保留指定的元素列表：")
        new_vb0_vertex_data = {}
        for offset in vb0_vertex_data:
            vertex_data_list = vb0_vertex_data.get(offset)
            new_vertex_data_list = []
            for vertex_data in vertex_data_list:
                """
                class VertexData:
                    vb_file_number = b"vb0"  # vb0
                    index = None
                    aligned_byte_offset = None
                    element_name = None
                    data = None
                """
                element_name = vertex_data.element_name
                if element_name in retain_element_list:
                    # print("重新设置vertex-data 中对应的alygned_byte_offset")
                    vertex_data.aligned_byte_offset = element_aligned_byte_offsets.get(element_name)

                    new_vertex_data_list.append(vertex_data)
            new_vb0_vertex_data[offset] = new_vertex_data_list
        print(new_vb0_vertex_data.get(b"0"))

        print("输出vb0文件")
        output_vb_fileinfo = VbFileInfo()
        """
        class VbFileInfo:
            header_info = HeaderInfo()
            vb0_vertex_data = {}
            output_filename = None
        """
        output_vb_fileinfo.header_info = header_info
        output_vb_fileinfo.vb0_vertex_data = new_vb0_vertex_data
        output_vb_fileinfo.output_filename = "output/"+ glob.glob(str(index) + '-vb0*txt')[0]

        # Write to vb file.
        output_model_txt(output_vb_fileinfo)



