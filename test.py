import torch
from skimage import io
from torch.autograd import Variable
from torch.utils.data import DataLoader
from torchvision import transforms
import time
from PIL import Image
import glob
from tqdm import tqdm

from data_loader import *

from model import ADMNet

def normPRED(x):
	MAX = torch.max(x)
	MIN = torch.min(x)

	out = (x-MIN)/(MAX-MIN)

	return out

def save_output(image_name,pred,d_dir):
	predict = pred
	predict = predict.squeeze()
	predict_np = predict.cpu().data.numpy()

	im = Image.fromarray(predict_np*255).convert('RGB')
	img_name = image_name.split("/")[-1]
	image = io.imread(image_name)
	imo = im.resize((image.shape[1],image.shape[0]),resample=Image.BILINEAR)

	t = img_name.split(".")
	t = t[0:-1]
	imidx = t[0]
	for i in range(1,len(t)):
		imidx = imidx + "." + t[i]

	imo.save(d_dir+imidx+'_Ours.png')


if __name__ == '__main__':
	# --------- Define the address and image format ---------
	image_dir = "/kaggle/input/duts-saliency-detection-dataset/DUTS-TE/DUTS-TE-Image"
	prediction_dir = ""
	model_dir = "/kaggle/working/L_ADMNet2024/model_save/ADMNet.pth"
	
	img_name_list = glob.glob(image_dir + '/*.jpg')
	
	# --------- Load the data ---------
	test_salobj_dataset = SalObjDataset(img_name_list = img_name_list, lbl_name_list = [],transform=transforms.Compose([Rescale(368),ToTensor(flag=0)]))
	test_salobj_dataloader = DataLoader(test_salobj_dataset, batch_size=1,shuffle=False,num_workers=1)
	
	# --------- Define the model ---------
	print("...load ADMNet...")
	net = ADMNet()
	net.load_state_dict(torch.load(model_dir, weights_only=True))

	#net.load_state_dict(torch.load(model_dir))
	if torch.cuda.is_available():
		net.cuda()
	net.eval()
	
	# --------- Generate prediction images ---------
	for i_test, data_test in tqdm(enumerate(test_salobj_dataloader)):
	
		inputs_test = data_test['image']
		inputs_test = inputs_test.type(torch.FloatTensor)
	
		if torch.cuda.is_available():
			inputs_test = Variable(inputs_test.cuda())
		else:
			inputs_test = Variable(inputs_test)
		if torch.cuda.is_available():
			torch.cuda.synchronize()
		start_time = time.time()
		d1, d2, d3, d4, d5 = net(inputs_test)
		if torch.cuda.is_available():
    			torch.cuda.synchronize()
		frame_time = time.time() - start_time
		tqdm.write(f"Frame time: {frame_time:.6f} seconds")  # Ensure print is visible
		# normalization
		pred = d1[:,0,:,:]
		pred = normPRED(pred)
             

		# save results to test_results folder
		save_output(img_name_list[i_test],pred,prediction_dir)
	
		del d1, d2, d3, d4, d5, inputs_test
