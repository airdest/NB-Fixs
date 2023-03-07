import os
import re
import glob
import shutil

class HeaderInfo:
    file_index = None
    stride = None
    first_vertex = None
    vertex_count = None
    topology = None

    # Header have many semantic element,like POSITION,NORMAL,COLOR etc.
    elementlist = None


class Element:
    semantic_name = None
    semantic_index = None
    format = None
    input_slot = None
    aligned_byte_offset = None
    input_slot_class = None
    instance_data_step_rate = None

    # the order of the element,start from 0.
    element_number = None

    # the byte length of this Element's data.
    byte_width = None


class VertexData:
    vb_file_number = b"vb0"  # vb0
    index = None
    aligned_byte_offset = None
    element_name = None
    data = None

    def __init__(self, line_bytes=b""):
        if line_bytes != b"":
            line_str = str(line_bytes.decode())
            # vb_file_number = line_str.split("[")[0]
            # because we vb_merge into one file, so it always be vb0
            vb_file_number = "vb0"
            self.vb_file_number = vb_file_number.encode()

            tmp_left_index = line_str.find("[")
            tmp_right_index = line_str.find("]")
            index = line_str[tmp_left_index + 1:tmp_right_index]
            self.index = index.encode()

            tmp_left_index = line_str.find("]+")
            aligned_byte_offset = line_str[tmp_left_index + 2:tmp_left_index + 2 + 3]
            self.aligned_byte_offset = aligned_byte_offset.encode()

            tmp_right_index = line_str.find(": ")
            element_name = line_str[tmp_left_index + 2 + 3 + 1:tmp_right_index]
            self.element_name = element_name.encode()

            tmp_left_index = line_str.find(": ")
            tmp_right_index = line_str.find("\r\n")
            data = line_str[tmp_left_index + 2:tmp_right_index]
            self.data = data.encode()

    def __str__(self):
        return self.vb_file_number + b"[" + self.index + b"]+" + self.aligned_byte_offset.decode().zfill(3).encode() + b" " + self.element_name + b": " + self.data + b"\r\n"


class VbFileInfo:
    header_info = HeaderInfo()
    vb0_vertex_data = {}
    output_filename = None


def get_header_info_by_elementnames(output_element_list):
    header_info = HeaderInfo()
    # 1.Generate element_list.
    element_list = []
    for element_name in output_element_list:
        element = Element()

        element.semantic_name = element_name
        element.input_slot = b"0"
        element.input_slot_class = b"per-vertex"
        element.instance_data_step_rate = b"0"

        if element_name.endswith(b"POSITION"):
            element.semantic_index = b"0"
            element.format = b"R32G32B32_FLOAT"
            element.byte_width = 12
        elif element_name.endswith(b"NORMAL"):
            element.semantic_index = b"0"
            element.format = b"R32G32B32_FLOAT"
            element.byte_width = 12
        elif element_name.endswith(b"TANGENT"):
            element.semantic_index = b"0"
            element.format = b"R32G32B32A32_FLOAT"
            element.byte_width = 16
        elif element_name.endswith(b"BLENDWEIGHTS"):
            element.semantic_index = b"0"
            element.format = b"R32G32B32A32_FLOAT"
            element.byte_width = 16
        elif element_name.endswith(b"BLENDINDICES"):
            element.semantic_index = b"0"
            element.format = b"R32G32B32A32_SINT"
            element.byte_width = 16
        elif element_name.endswith(b"COLOR"):
            element.semantic_index = b"0"
            element.format = b"R8G8B8A8_UNORM"
            element.byte_width = 4
        elif element_name.endswith(b"TEXCOORD"):
            element.semantic_index = b"0"
            element.format = b"R32G32_FLOAT"
            element.byte_width = 8
        elif element_name.endswith(b"TEXCOORD1"):
            element.semantic_index = b"1"
            element.format = b"R32G32_FLOAT"
            element.byte_width = 8

        element_list.append(element)
    # 2.Add aligned_byte_offset and element_number.
    new_element_list = []
    aligned_byte_offset = 0
    for index in range(len(element_list)):
        element = element_list[index]
        element.element_number = str(index).encode()
        element.aligned_byte_offset = str(aligned_byte_offset).encode()
        aligned_byte_offset = aligned_byte_offset + element.byte_width
        new_element_list.append(element)

    # 3.Set element_list and stride.
    header_info.first_vertex = b"0"
    header_info.topology = b"trianglelist"
    header_info.stride = str(aligned_byte_offset).encode()
    header_info.elementlist = new_element_list

    return header_info


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

