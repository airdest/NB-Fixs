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
            if self.semantic_index == b"0":
                self.byte_width = 8
            else:
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


GLOBAL_ELEMENT_NUMBER = None


def get_header_info(vb_file_name):

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

            if element_tmp.element_number == GLOBAL_ELEMENT_NUMBER and elements_single_process_over:
                header_info.elementlist = element_list
                elements_all_process_over = True
                break

    # safely close the file.
    vb_file.close()
    return header_info


def split_file(source_name):
    vb_name = source_name + ".vb"
    fmt_name = source_name + ".fmt"

    vb_file = open(vb_name, "rb")
    vb_file_buffer = vb_file.read()
    vb_file.close()

    header_info = get_header_info(fmt_name)

    # fmt文件的原始步长
    combined_stride = int(header_info.stride.decode())

    # vertex_data的数量
    vertex_count = int(len(vb_file_buffer) / combined_stride)

    # aligned_byte_offsets
    offset_list = []

    # strides
    width_list = []

    for element in header_info.elementlist:
        offset_list.append(int(element.aligned_byte_offset.decode()))
        width_list.append(element.byte_width)
    print(width_list)

    # use to store parsed vertex_data.
    vertex_data_list = [[] for i in range(vertex_count)]

    # parse vertex_data,load into vertex_data_list.
    for index in range(len(width_list)):
        for i in range(vertex_count):
            start_index = i * combined_stride + offset_list[index]
            vertex_data = vb_file_buffer[start_index:start_index + width_list[index]]
            vertex_data_list[i].append(vertex_data)

    print(vertex_data_list[0])

    # parse vertex_data_list，and load vb0,vb1,vb2
    vb0_vertex_data = [[] for i in range(vertex_count)]
    vb1_vertex_data = [[] for i in range(vertex_count)]
    vb2_vertex_data = [[] for i in range(vertex_count)]

    """
    vb0 for POSITION，NORMAL。TANGENT
    vb1 for BLENDWEIGHTS，BLENDINDICES
    vb2 for TEXCOORD
    """
    for index in range(len(width_list)):
        for i in range(vertex_count):
            # POSITION
            if index == 0:
                vb0_vertex_data[i].append(vertex_data_list[i][0])
            # NORMAL
            if index == 1:
                vb0_vertex_data[i].append(vertex_data_list[i][1])
            # TANGENT
            if index == 2:
                vb0_vertex_data[i].append(vertex_data_list[i][2])

            # BLENDWEIGHT
            if index == 3:
                vb1_vertex_data[i].append(vertex_data_list[i][3])
            # BLENDINDICES
            if index == 4:
                vb1_vertex_data[i].append(vertex_data_list[i][4])

            # TEXCOORD
            if index == 5:
                vb2_vertex_data[i].append(vertex_data_list[i][5])

    vb0_bytes = b""
    for vertex_data in vb0_vertex_data:
        for data in vertex_data:
            vb0_bytes = vb0_bytes + data
    vb1_bytes = b""
    for vertex_data in vb1_vertex_data:
        for data in vertex_data:
            vb1_bytes = vb1_bytes + data
    vb2_bytes = b""
    for vertex_data in vb2_vertex_data:
        for data in vertex_data:
            vb2_bytes = vb2_bytes + data

    output_vb0_filename = source_name + "_POSITION.buf"
    output_vb1_filename = source_name + "_BLEND.buf"
    output_vb2_filename = source_name + "_TEXCOORD.buf"

    with open(output_vb0_filename, "wb+") as output_vb0_file:
        output_vb0_file.write(vb0_bytes)
    with open(output_vb1_filename, "wb+") as output_vb1_file:
        output_vb1_file.write(vb1_bytes)
    with open(output_vb2_filename, "wb+") as output_vb2_file:
        output_vb2_file.write(vb2_bytes)


if __name__ == "__main__":
    # set work dir.
    work_dir = "C:/Users/Administrator/Desktop/NBLoaderV1.1/NarakaTest/"
    os.chdir(work_dir)

    # set element number ,Naraka must be 5.
    GLOBAL_ELEMENT_NUMBER = b"5"

    # combine the output filename.
    source_names = ["cloth"]
    for source_name in source_names:
        split_file(source_name)
