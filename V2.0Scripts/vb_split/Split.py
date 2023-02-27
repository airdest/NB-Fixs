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
import glob
import os
import re
import json


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

    def revise(self):
        if self.semantic_name == b"POSITION":
            self.byte_width = 12
        if self.semantic_name == b"NORMAL":
            self.byte_width = 12
        if self.semantic_name == b"TANGENT":
            self.byte_width = 16
        if self.semantic_name == b"COLOR":
            self.byte_width = 4
        if self.semantic_name == b"TEXCOORD":
            self.byte_width = 8
        if self.semantic_name == b"BLENDWEIGHTS":
            self.byte_width = 16
        if self.semantic_name == b"BLENDINDICES":
            self.byte_width = 16


class HeaderInfo:
    file_index = None
    stride = None
    first_vertex = None
    vertex_count = None
    topology = None

    # Header have many semantic element,like POSITION,NORMAL,COLOR etc.
    elementlist = None


def get_header_info(vb_file_name, max_element_number):
    """
    :param vb_file_name: 要分割的vb文件名称
    :param max_element_number:  byte类型，例如b"5"，代表读取的fmt文件一共有6个元素，因为是从0开始的
    :return:
    """
    vb_file = open(vb_file_name, 'rb')

    header_info = HeaderInfo()

    header_process_over = False

    elements_all_process_over = False
    elements_single_process_over = False

    element_list = []

    element_tmp = Element()

    while vb_file.tell() < os.path.getsize(vb_file.name):
        # read a line to process.
        line = vb_file.readline()
        # process Headerinfo part.
        if not header_process_over:

            if line.startswith(b"stride: "):
                stride = line[line.find(b"stride") + b"stride: ".__len__():line.find(b"\r\n")]
                header_info.stride = stride
            # set first_vertex
            if line.startswith(b"first vertex: "):
                first_vertex = line[line.find(b"first vertex: ") + b"first vertex: ".__len__():line.find(b"\r\n")]
                header_info.first_vertex = first_vertex
            # set vertex_count
            if line.startswith(b"vertex count: "):
                vertex_count = line[line.find(b"vertex count: ") + b"vertex count: ".__len__():line.find(b"\r\n")]
                header_info.vertex_count = vertex_count
            # set topology
            if line.startswith(b"topology: "):
                topology = line[line.find(b"topology: ") + b"topology: ".__len__():line.find(b"\r\n")]
                header_info.topology = topology

            if header_info.topology is not None:
                header_process_over = True

        # process Element part.
        if not elements_all_process_over:

            if line.startswith(b"element["):
                # start a new element process.
                elements_single_process_over = False

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
                # must be all zero
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
                # revise bytewidth.
                element_tmp.revise()
                # element_tmp append to list.
                element_list.append(element_tmp)
                # single element process over.
                elements_single_process_over = True

            if element_tmp.element_number == max_element_number and elements_single_process_over:
                header_info.elementlist = element_list
                elements_all_process_over = True
                break

    # safely close the file.
    vb_file.close()
    return header_info


def split_file(source_name, max_element_number=b"5"):
    """
    :param source_name:
    :param max_element_number:  要从fmt文件中读取的最大的element的索引，从0开始读取到这个最大索引结束
    # set element number ,Naraka will be 5 ,and plus TEXCOORD 1 ,it will be 6.
    这里是5的原因是有6个元素：
    POSITION、NORMAL、TANGENT、BLENDWEIGHTS、BLENDINDICES、TEXCOORD
    有一些模型包含多个TEXCOORD，比如殷紫萍红皮上衣包含TEXCOORD和TEXCOORD1，此时设为6

    这里之所以要手动指定一个数字，是因为有时重新导入到游戏中时，在存在多个TEXCOORD的情况下，只有第一个TEXCOORD是有用的
    比如TEXCOORD1的索引为b"6"，则我们只需要读取到b"5"的TEXCOORD就够了，所以这里的数字由人为手动控制，便于调试
    关于第二个TEXCOORD1并未导入游戏导致模型变成透明，这一点还需验证
    :return:
    """
    vb_name = source_name + ".vb"
    fmt_name = source_name + ".fmt"

    vb_file = open(vb_name, "rb")
    vb_file_buffer = vb_file.read()
    vb_file.close()

    header_info = get_header_info(fmt_name, max_element_number)

    # fmt文件的原始步长
    combined_stride = int(header_info.stride.decode())

    # vertex_data的数量
    vertex_count = int(len(vb_file_buffer) / combined_stride)

    # aligned_byte_offsets
    offset_list = []

    # strides
    width_list = []

    # element_names
    element_name_list = []

    for element in header_info.elementlist:
        offset_list.append(int(element.aligned_byte_offset.decode()))
        width_list.append(element.byte_width)
        if element.semantic_index == b"0":
            element_name_list.append(element.semantic_name)
        else:
            element_name_list.append(element.semantic_name + element.semantic_index)

    # print(width_list)
    # print(element_name_list)

    # use to store parsed vertex_data.
    vertex_data_list = [[] for i in range(vertex_count)]

    # parse vertex_data,load into vertex_data_list.
    for index in range(len(width_list)):
        for i in range(vertex_count):
            start_index = i * combined_stride + offset_list[index]
            vertex_data = vb_file_buffer[start_index:start_index + width_list[index]]
            vertex_data_list[i].append(vertex_data)

    # print(vertex_data_list[0])

    position_vertex_data = [[] for i in range(vertex_count)]
    blend_vertex_data = [[] for i in range(vertex_count)]
    texcoord_vertex_data = [[] for i in range(vertex_count)]

    for index in range(len(width_list)):
        for i in range(vertex_count):
            if element_name_list[index] in [b"POSITION", b"NORMAL", b"TANGENT"]:
                position_vertex_data[i].append(vertex_data_list[i][index])

            if element_name_list[index] in [b"BLENDWEIGHTS", b"BLENDINDICES"]:
                blend_vertex_data[i].append(vertex_data_list[i][index])

            if element_name_list[index] in [b"TEXCOORD", b"TEXCOORD1"]:
                texcoord_vertex_data[i].append(vertex_data_list[i][index])

    position_bytes = b""
    for vertex_data in position_vertex_data:
        for data in vertex_data:
            position_bytes = position_bytes + data

    blend_bytes = b""
    for vertex_data in blend_vertex_data:
        for data in vertex_data:
            blend_bytes = blend_bytes + data

    texcoord_bytes = b""
    for vertex_data in texcoord_vertex_data:
        for data in vertex_data:
            texcoord_bytes = texcoord_bytes + data

    output_position_filename = source_name + "_POSITION.buf"
    output_blend_filename = source_name + "_BLEND.buf"
    output_texcoord_filename = source_name + "_TEXCOORD.buf"

    with open(output_position_filename, "wb+") as output_position_file:
        output_position_file.write(position_bytes)
    with open(output_blend_filename, "wb+") as output_blend_file:
        output_blend_file.write(blend_bytes)
    with open(output_texcoord_filename, "wb+") as output_texcoord_file:
        output_texcoord_file.write(texcoord_bytes)


if __name__ == "__main__":
    # set work dir.
    work_dir = "C:/Users/Administrator/Desktop/NarakaLoaderV1.1/NarakaTest/"
    os.chdir(work_dir)

    # combine the output filename.
    source_names = ["cloth"]

    for source_name in source_names:
        print("Processing " + source_name + ".vb")
        split_file(source_name, max_element_number=b"5")

    print("----------------------------------------------------------\r\nAll process done！")