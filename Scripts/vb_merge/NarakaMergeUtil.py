import re
import glob
import os
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
    vertex_data_chunk_list = [[VertexData()]]
    output_filename = None


def get_header_info(vb_file_name, max_element_number):

    vb_file = open(vb_file_name, 'rb')

    header_info = HeaderInfo()

    # Use to control the header process.
    header_process_over = False
    # Use to control the element process.
    elements_all_process_over = False
    elements_single_process_over = False

    element_list = []

    element_tmp = Element()

    while vb_file.tell() < os.path.getsize(vb_file.name):
        # Read a line.
        line = vb_file.readline()
        # Process header part.
        if not header_process_over:
            # Set the fitst vertex,because this value in every vb file is totally same,so we get the final file's first vertex is safe.
            if line.startswith(b"first vertex: "):
                first_vertex = line[line.find(b"first vertex: ") + b"first vertex: ".__len__():line.find(b"\r\n")]
                header_info.first_vertex = first_vertex
            # Set vertex count, similarly it's safe to get the final vb file's vertex count.
            if line.startswith(b"vertex count: "):
                vertex_count = line[line.find(b"vertex count: ") + b"vertex count: ".__len__():line.find(b"\r\n")]
                header_info.vertex_count = vertex_count
            # Set topology, similarly it's safe to get the final vb file's vertex count.
            if line.startswith(b"topology: "):
                topology = line[line.find(b"topology: ") + b"topology: ".__len__():line.find(b"\r\n")]
                header_info.topology = topology

            if header_info.topology is not None:
                header_process_over = True

        # Process element list.
        if not elements_all_process_over:

            if line.startswith(b"element["):
                # If detected "element[" ,that means we start to process a new element.
                elements_single_process_over = False
                # Initialize ElementTmp
                element_tmp = Element()
                element_number = line[line.find(b"element[") + b"element[".__len__():line.find(b"]:\r\n")]
                element_tmp.element_number = element_number
            if line.startswith(b"  SemanticName: "):
                semantic_name = line[line.find(b"  SemanticName: ") + b"  SemanticName: ".__len__():line.find(b"\r\n")]
                element_tmp.semantic_name = semantic_name
            if line.startswith(b"  SemanticIndex: "):
                semantic_index = line[
                                 line.find(b"  SemanticIndex: ") + b"  SemanticIndex: ".__len__():line.find(b"\r\n")]
                element_tmp.semantic_index = semantic_index
            if line.startswith(b"  Format: "):
                format = line[line.find(b"  Format: ") + b"  Format: ".__len__():line.find(b"\r\n")]
                element_tmp.format = format
            if line.startswith(b"  InputSlot: "):
                input_slot = line[line.find(b"  InputSlot: ") + b"  InputSlot: ".__len__():line.find(b"\r\n")]
                element_tmp.input_slot = input_slot
                # Because we finally get only one vb file,so every input_slot should be set to 0.
                element_tmp.input_slot = b"0"
            if line.startswith(b"  AlignedByteOffset: "):
                aligned_byte_offset = line[line.find(
                    b"  AlignedByteOffset: ") + b"  AlignedByteOffset: ".__len__():line.find(b"\r\n")]
                element_tmp.aligned_byte_offset = aligned_byte_offset
            if line.startswith(b"  InputSlotClass: "):
                input_slot_class = line[line.find(b"  InputSlotClass: ") + b"  InputSlotClass: ".__len__():line.find(
                    b"\r\n")]
                element_tmp.input_slot_class = input_slot_class
            if line.startswith(b"  InstanceDataStepRate: "):
                instance_data_step_rate = line[line.find(
                    b"  InstanceDataStepRate: ") + b"  InstanceDataStepRate: ".__len__():line.find(b"\r\n")]
                element_tmp.instance_data_step_rate = instance_data_step_rate

                # Put element_tmp into element_list.
                element_list.append(element_tmp)
                # Process single element over.
                elements_single_process_over = True

            if element_tmp.element_number == max_element_number and elements_single_process_over:
                header_info.elementlist = element_list
                elements_all_process_over = True
                break

    # Safely close the file.
    vb_file.close()
    return header_info


def read_vertex_data_chunk_list_gracefully(file_index, read_element_list, only_vb1=False, sanity_check=False):
    """
    :param file_index:  the file index numbers you want to process.
    :param read_element_list:  the element name list you need to read.
    :param only_vb1:  weather read only from vb slot 1 file.
    :param sanity_check: weather check the first line to remove duplicated content.
    :return:
    """
    # Get vb filenames by the file_index.
    if only_vb1:
        vb_filenames = sorted(glob.glob(file_index + '-vb1*txt'))
    else:
        vb_filenames = sorted(glob.glob(file_index + '-vb*txt'))

    print("开始读取vertex-data部分：")
    print("file_index: " + str(file_index))
    print("vb_filenames: " + str(vb_filenames))

    header_info = get_header_info(vb_filenames[0], b"9")
    vertex_count = header_info.vertex_count

    vertex_data_chunk_list = [[] for i in range(int(str(vertex_count.decode())))]

    # temp vertex_data_chunk
    vertex_data_chunk = []

    chunk_index = 0

    for filename in vb_filenames:
        # Get the vb file's slot number.
        vb_number = filename[filename.find("-vb"):filename.find("=")][1:].encode()
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
                chunk_index = int(vertex_data.index.decode())

            # Process when meet the \r\n.
            if (line.startswith(b"\r\n") or vb_file.tell() == vb_file_size) and line_before_tmp.startswith(vb_number):

                line_before_tmp = b"\r\n"

                # If we got \r\n,it means this vertex_data_chunk as ended,so put it into the final vertex_data_chunk_list.
                vertex_data_chunk_list[chunk_index].append(vertex_data_chunk)

                # Reset temp VertexData
                vertex_data_chunk = []

            if vb_file.tell() == vb_file_size:
                break
        vb_file.close()

    # Combine every chunk split part by corresponding index.
    new_vertex_data_chunk_list = []
    for vertex_data_chunk in vertex_data_chunk_list:
        new_vertex_data_chunk = []
        for vertex_data_chunk_split in vertex_data_chunk:
            for vertex_data in vertex_data_chunk_split:
                new_vertex_data_chunk.append(vertex_data)
        new_vertex_data_chunk_list.append(new_vertex_data_chunk)
    vertex_data_chunk_list = new_vertex_data_chunk_list

    # Check TEXCOORD and remove duplicated content.
    # TODO 这里要添加一种情况，那就是存在多个TEXCOORD的同时，所有TEXCOORD还都是0，0
    #  判断如果是TEXCOORD，则允许内容重复
    if sanity_check:
        vertex_data_chunk_check = vertex_data_chunk_list[0]
        # Count every time the different kind of data appears.
        repeat_value_time = {}
        for vertex_data in vertex_data_chunk_check:
            if repeat_value_time.get(vertex_data.data) is None:
                repeat_value_time[vertex_data.data] = 1
            else:
                repeat_value_time[vertex_data.data] = repeat_value_time[vertex_data.data] + 1

        # Decide the unique element_name by the data appears time.
        unique_element_names = []
        for vertex_data in vertex_data_chunk_check:
            # 这里新增了，认为所有的TEXCOORD都是独一无二的，经过测试，这样是行不通的
            # if repeat_value_time.get(vertex_data.data) == 1 or vertex_data.element_name.startswith(b"TEXCOORD"):
            if repeat_value_time.get(vertex_data.data) == 1:
                unique_element_names.append(vertex_data.element_name)

        # Retain vertex_data based on the unique element name.
        new_vertex_data_chunk_list = []
        for vertex_data_chunk in vertex_data_chunk_list:
            new_vertex_data_chunk = []
            for vertex_data in vertex_data_chunk:
                if vertex_data.element_name in unique_element_names:
                    new_vertex_data_chunk.append(vertex_data)
            new_vertex_data_chunk_list.append(new_vertex_data_chunk)
        vertex_data_chunk_list = new_vertex_data_chunk_list

    # Retain some content based on the input element_list.
    revised_vertex_data_chunk_list = []
    for index in range(len(vertex_data_chunk_list)):
        vertex_data_chunk = vertex_data_chunk_list[index]
        new_vertex_data_chunk = []
        for vertex_data in vertex_data_chunk:
            if vertex_data.element_name in read_element_list:
                new_vertex_data_chunk.append(vertex_data)
        revised_vertex_data_chunk_list.append(new_vertex_data_chunk)

    return revised_vertex_data_chunk_list


def output_model_txt(vb_file_info):
    header_info = vb_file_info.header_info
    vertex_data_chunk_list = vb_file_info.vertex_data_chunk_list
    output_filename = vb_file_info.output_filename

    print("Starting output to file: " + output_filename)
    # Grab the first vertex_data, and judge which element exists.
    vertex_data_chunk_test = vertex_data_chunk_list[0]
    vertex_data_chunk_has_element_list = []
    # Default we think all element does not exist,unless we detected it.
    for vertex_data in vertex_data_chunk_test:
        vertex_data_chunk_has_element_list.append(vertex_data.element_name)

    # Get the element list which can be output.
    header_info_has_element_list = []
    for element in header_info.elementlist:
        name = element.semantic_name
        if element.semantic_name == b"TEXCOORD" and element.semantic_index != b"0":
                name = element.semantic_name + element.semantic_index
        header_info_has_element_list.append(name)

    # Output to the final file.
    output_file = open(output_filename, "wb+")

    # (1) First output header.
    output_file.write(b"stride: " + header_info.stride + b"\r\n")
    output_file.write(b"first vertex: " + header_info.first_vertex + b"\r\n")
    output_file.write(b"vertex count: " + header_info.vertex_count + b"\r\n")
    output_file.write(b"topology: " + header_info.topology + b"\r\n")

    # (2) Traversal Elementlist,if element exists then output it.
    element_list = header_info.elementlist
    for element in element_list:
        element_name = element.semantic_name
        semantic_index = element.semantic_index
        if element_name == b"TEXCOORD":
            if semantic_index != b'0':
                element_name = element_name + semantic_index

        if vertex_data_chunk_has_element_list.__contains__(element_name):
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

    # It's element_name must appear in header_info_has_element_list,otherwise it can't be output.
    for index in range(len(vertex_data_chunk_list)):
        vertex_data = vertex_data_chunk_list[index]

        for vertex_data in vertex_data:
            if header_info_has_element_list.__contains__(vertex_data.element_name):
                output_file.write(vertex_data.__str__())

        # If it is the final line ,we don't append \r\n.
        if index != len(vertex_data_chunk_list) - 1:
            output_file.write(b"\r\n")

    output_file.close()


def move_related_files(indices, move_dds=False, only_pst7=False, move_vscb=False, move_pscb=False):
    """
    :param indices:  the file indix you want to move
    :param move_dds: weather move dds file.
    :param only_pst7: weather only move ps-t7 dds file.
    :param move_vscb:
    :param move_pscb:
    :return:
    """
    # Create output folder in case it doesn't exist.
    if not os.path.exists('output'):
        os.mkdir('output')

    if move_dds:
        print("----------------------------------------------------------------")
        print("Start to move .dds files.")
        # Start to move .dds files.
        if only_pst7:
            filenames = glob.glob('*ps-t7*.dds')
        else:
            filenames = glob.glob('*.dds')

        for filename in filenames:
            if os.path.exists(filename):
                for index in indices:
                    if filename.__contains__(index):
                        # print("Moving ： " + filename + " ....")
                        shutil.copy2(filename, 'output/' + filename)

    if move_vscb:
        print("----------------------------------------------------------------")
        print("Start to move VS-CB files.")
        # Start to move VS-CB files.
        filenames = glob.glob('*vs-cb*')
        for filename in filenames:
            if os.path.exists(filename):
                # Must have the vb index you sepcified.
                for index in indices:
                    if filename.__contains__(index):
                        # print("Moving ： " + filename + " ....")
                        shutil.copy2(filename, 'output/' + filename)

    if move_pscb:
        print("----------------------------------------------------------------")
        print("Start to move PS-CB files.")
        # Start to move PS-CB files.
        filenames = glob.glob('*ps-cb*')
        for filename in filenames:
            if os.path.exists(filename):
                # Must have the vb index you sepcified.
                for index in indices:
                    if filename.__contains__(index):
                        # print("Moving ： " + filename + " ....")
                        shutil.copy2(filename, 'output/' + filename)


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


def get_ib_bytes_by_indices(indices):
    ib_filenames = []
    for index in range(len(indices)):
        indexnumber = indices[index]
        ib_filename = sorted(glob.glob(str(indexnumber) + '-ib*txt'))[0]
        ib_filenames.append(ib_filename)

    ib_file_bytes = []
    for ib_filename in ib_filenames:
        with open(ib_filename, "rb") as ib_file:
            bytes = ib_file.read()
            if bytes not in ib_file_bytes:
                ib_file_bytes.append(bytes)

    return ib_file_bytes


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
