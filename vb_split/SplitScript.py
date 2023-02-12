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
                # TODO 测试它的原始R8G8B8A8_UNORM 是否能正确导入
                # element.format = b"R32G32B32A32_FLOAT"
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

    # 用于控制标题部分读取
    header_process_over = False
    # 用于控制Elements部分读取
    elements_all_process_over = False
    elements_single_process_over = False
    # 用来装element列表
    element_list = []
    # 用来临时装一个Element
    element_tmp = Element()

    while vb_file.tell() < os.path.getsize(vb_file.name):
        # 读取一行
        line = vb_file.readline()
        # 处理header
        if not header_process_over:
            # TODO 这里不够兼容，因为不能处理first vertex在各个vb文件中不同的情况，具体后续再测试吧
            if line.startswith(b"stride: "):
                stride = line[line.find(b"stride") + b"stride: ".__len__():line.find(b"\r\n")]
                header_info.stride = stride
            # 设置first_vertex,因为所有文件的first_vertex都是相同的，都是0，所以这里会取最后一次的first_vertex
            if line.startswith(b"first vertex: "):
                first_vertex = line[line.find(b"first vertex: ") + b"first vertex: ".__len__():line.find(b"\r\n")]
                header_info.first_vertex = first_vertex
            # 设置vertex_count,因为所有文件的vertex_count都是相同的，所以这里会取最后一次的vertex_count
            if line.startswith(b"vertex count: "):
                vertex_count = line[line.find(b"vertex count: ") + b"vertex count: ".__len__():line.find(b"\r\n")]
                header_info.vertex_count = vertex_count
            # 设置topology,因为所有文件的topology都是相同的，所以这里会取最后一次的topology
            if line.startswith(b"topology: "):
                topology = line[line.find(b"topology: ") + b"topology: ".__len__():line.find(b"\r\n")]
                header_info.topology = topology

            if header_info.topology is not None:
                header_process_over = True

        # 处理Element部分,同理，所有vb0,1,2这样文件的element部分都是完全相同的，所以默认赋值的最后一个也是正确的
        if not elements_all_process_over:

            if line.startswith(b"element["):
                # 检测到element[  说明开始了新的element处理
                elements_single_process_over = False
                # 初始化ElementTmp
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
                # 因为最终都在一个文件里面，所以所有的input_slot都设置为0
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
                # 加入之前修正bytewidth
                element_tmp.revise()
                # element_tmp加入list
                element_list.append(element_tmp)
                # 单个处理完毕
                elements_single_process_over = True

            if element_tmp.element_number == GLOBAL_ELEMENT_NUMBER and elements_single_process_over:
                header_info.elementlist = element_list
                elements_all_process_over = True
                break

    # 读取完header部分后，关闭文件
    vb_file.close()
    return header_info


if __name__ == "__main__":
    # 设置工作目录
    work_dir = "C:/Users/Administrator/Desktop/NarakaTest/"
    os.chdir(work_dir)

    # 设置常量
    GLOBAL_ELEMENT_NUMBER = b"5"

    # 各文件名称
    source_name = "body"
    vb_name = source_name + ".vb"
    fmt_name = source_name + ".fmt"
    ib_name = source_name + ".ib"

    vb_file = open(vb_name, "rb")
    vb_file_buffer = vb_file.read()
    vb_file.close()

    # TODO 首先解析FMT文件，读取按顺序的Element元素信息
    header_info = get_header_info(fmt_name)

    # TODO 首先要明确这个vertex-data最终要拆分成几部分：
    # TODO vb0, vb1, vb2
    # TODO 目前可以确定vb1只有TEXCOORD一个属性，接下来就看BLENDWIDTH和BLENDINDICES放哪儿了
    """
    elementnumber分别是
    vb0存放POSITION，NORMAL。TANGENT，COLOR （测试TEXCOORD1） 0,1,2,3,5
    vb1存放TEXCOORD  4  
    vb2存放BLENDWEIGHTS，BLENDINDICES  6,7
    """

    # fmt文件的原始步长

    combined_stride = int(header_info.stride.decode())

    # vertex_data的数量
    vertex_count = int(len(vb_file_buffer) / combined_stride)

    # aligned_byte_offsets
    offset_list = []

    # strides
    width_list = []

    # 初始化offset_list和width_list，方便后续使用
    for element in header_info.elementlist:
        offset_list.append(int(element.aligned_byte_offset.decode()))
        width_list.append(element.byte_width)
    print(width_list)

    # 用来存放解析好的vertex_data
    vertex_data_list = [[] for i in range(vertex_count)]


    # 解析vertex_data并装入vertex_data_list
    for index in range(len(width_list)):
        for i in range(vertex_count):
            start_index = i * combined_stride + offset_list[index]
            vertex_data = vb_file_buffer[start_index:start_index + width_list[index]]
            vertex_data_list[i].append(vertex_data)

    print(vertex_data_list[0])

    # 解析vertex_data_list，分别装载vb0,vb1,vb2
    vb0_vertex_data = [[] for i in range(vertex_count)]
    vb1_vertex_data = [[] for i in range(vertex_count)]
    vb2_vertex_data = [[] for i in range(vertex_count)]

    for index in range(len(width_list)):
        for i in range(vertex_count):
            # TODO POSITION
            # POSITION
            if index == 0:
                vb0_vertex_data[i].append(vertex_data_list[i][0])
            # NORMAL
            if index == 1:
                vb0_vertex_data[i].append(vertex_data_list[i][1])
            # TANGENT
            if index == 2:
                vb0_vertex_data[i].append(vertex_data_list[i][2])

            # TODO BLEND
            # BLENDWEIGHT
            if index == 3:
                vb1_vertex_data[i].append(vertex_data_list[i][3])
            # BLENDINDICES
            if index == 4:
                vb1_vertex_data[i].append(vertex_data_list[i][4])

            # TODO TEXCOORD 但为什么stride是12？？？难道COLOR不需要？这里永劫干脆就没有COLOR
            # TEXCOORD
            if index == 5:
                vb2_vertex_data[i].append(vertex_data_list[i][5])

            # # TEXCOORD
            # if index == 6:
            #     vb2_vertex_data[i].append(vertex_data_list[i][6])
            # # TEXCOORD1
            # if index == 7:
            #     vb2_vertex_data[i].append(vertex_data_list[i][7])


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
